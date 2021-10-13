import datetime
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db.models import Avg
from django.contrib.auth import get_user_model
from ratings.models import Team, TeamRating, TeamRatingHistory, Match, Prediction
from ratings.management.LeagueOfElo.league_of_elo.elo.rating_system import Elo


SPRING_RESET = -1
SUMMER_RESET = -2
INTL_TOURNAMENT = -3


class StaleRatingWarning(Exception):
    pass


class Command(BaseCommand):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.elo_model = Elo(K=30, score_mult=True)
        self.elo_user = get_user_model().objects.get(username='LeagueOfElo')
        self.prev_match_region = None

    def add_arguments(self, parser):
        parser.add_argument('--clear_ratings', action='store_true', help='Deletes all Team Ratings from database.')

    def _inter_season_reset(self, reset_date, inactive_cutoff_date):
        print(f'\nSeason reset: {reset_date}')
        regional_averages = {
            'NA': 1500,
            'EU': 1500,
            'KR': 1500,
            'CN': 1500,
            'INT': 1500}
        active_teams = TeamRating.objects.filter(rating_date__gte=inactive_cutoff_date)
        reg_avg = active_teams.values('team__region').annotate(rating=Avg('rating'))
        for entry in reg_avg:
            regional_averages[entry['team__region']] = entry['rating']

        for active_team in active_teams:
            team_regional_avg = regional_averages[active_team.team.region]
            new_rating = 0.75 * active_team.rating + 0.25 * team_regional_avg
            TeamRating.objects.filter(team=active_team.team).update(rating=new_rating, rating_date=reset_date)
            print(f'\nUpdating {active_team.team} rating from {active_team.rating:.2f} to {new_rating:.2f}')

    def _continuity_check(self, team, match_date):
        continuity_teams = Team.objects.filter(team_continuity_id=team.team_continuity_id)
        if not TeamRating.objects.filter(team__in=continuity_teams).exists():
            new_team = TeamRating(team=team, rating=1500, rating_date=match_date - datetime.timedelta(days=1))
            new_team.save()
            last_reset_index = TeamRatingHistory.objects.filter(team__short_name='NUL').order_by('-rating_index').first().rating_index if TeamRatingHistory.objects.all().exists() else 0
            TeamRatingHistory(team=team, match=None, rating_index=last_reset_index, rating=new_team.rating).save()
            print(f'\nCreated {new_team}')
        else:
            most_recent_rating = TeamRating.objects.filter(team__in=continuity_teams).order_by('-rating_date')[0]
            Team.objects.filter(pk=most_recent_rating.team.pk).update(is_active=False)
            updated_rating, _ = TeamRating.objects.update_or_create(team=team,
                    defaults={'rating':most_recent_rating.rating, 'rating_date':most_recent_rating.rating_date})
            rating_index = TeamRatingHistory.objects.filter(team__in=continuity_teams).order_by('-rating_index').first().rating_index
            TeamRatingHistory(team=team, match=None, rating_index=rating_index, rating=updated_rating.rating).save()
            print(f'\nSet {updated_rating} from {most_recent_rating}')

    def _set_prediction(self, match):
        if match.match_info == 'inter_season_reset':
            return
        try:
            t1_rating = TeamRating.objects.get(team=match.team1).rating
        except (ObjectDoesNotExist):
            t1_rating = 1500
        try:
            t2_rating = TeamRating.objects.get(team=match.team2).rating
        except (ObjectDoesNotExist):
            t2_rating = 1500
        prediction = self.elo_model.predict(t1_rating, t2_rating)
        Prediction.objects.update_or_create(user=self.elo_user, match=match, defaults={'predicted_t1_win_prob': prediction})

    def _process_match(self, match):
        if match.start_timestamp > timezone.now():
            self._set_prediction(match)
            print('F', end='', flush=True) # F for future
            return False

        if match.elo_processed:
            print('A', end='', flush=True) # A for already processed
            return False

        if match.match_info == 'inter_season_reset':
            # Need to differentiate between spring and summer reset so inactive teams don't get
            # considered active due to these rating updates.
            if match.team1_score == SPRING_RESET:
                inactive_cutoff_date = match.start_timestamp - datetime.timedelta(days=180)
                self._inter_season_reset(match.start_timestamp, inactive_cutoff_date)
            elif match.team1_score == SUMMER_RESET:
                inactive_cutoff_date = match.start_timestamp - datetime.timedelta(days=120)
                self._inter_season_reset(match.start_timestamp, inactive_cutoff_date)
            else: #INTL_TOURNAMENT
                pass
            Match.objects.filter(pk=match.pk).update(elo_processed=True)
            return True

        stale_rating_cutoff = match.start_timestamp - datetime.timedelta(days=90)
        for team in [match.team1, match.team2]:
            try:
                rating = TeamRating.objects.get(team=team)
                if rating.rating_date < stale_rating_cutoff:
                    raise StaleRatingWarning
            except (ObjectDoesNotExist, StaleRatingWarning):
                self._continuity_check(team, match.start_timestamp)
            Team.objects.filter(pk=team.pk).update(is_active=True)
        t1_rating = TeamRating.objects.get(team=match.team1)
        t2_rating = TeamRating.objects.get(team=match.team2)

        if match.start_timestamp <= t1_rating.rating_date:
            print('E', end='', flush=True) # Team rating newer than match. We should never see this.
            return False
        if match.team1_score == 0 and match.team2_score == 0:
            print('N', end='', flush=True) # Match results not recorded yet.
            return False

        prediction = self.elo_model.predict(t1_rating.rating, t2_rating.rating)
        if match.team1_score > match.team2_score:
            match_outcome = 1.0
        elif match.team1_score < match.team2_score:
            match_outcome = 0.0
        else:
            match_outcome = 0.5
        brier = (match_outcome - prediction)**2
        Prediction.objects.update_or_create(user=self.elo_user, match=match, defaults={'predicted_t1_win_prob': prediction, 'brier': brier})

        t1_adj, t2_adj = self.elo_model.process_outcome(t1_rating.rating, t2_rating.rating, match.team1_score, match.team2_score)
        TeamRating.objects.filter(team=match.team1).update(rating=t1_rating.rating + t1_adj, rating_date=match.start_timestamp)
        TeamRating.objects.filter(team=match.team2).update(rating=t2_rating.rating + t2_adj, rating_date=match.start_timestamp)
        Match.objects.filter(pk=match.pk).update(elo_processed=True)
        print('.', end='', flush=True)
        return True

    def _update_rating_history(self, match, prev_match_region):
        if match.match_info == 'inter_season_reset' or (match.region == 'INT' and self.prev_match_region != 'INT'):
            # Season sync
            rating_index = TeamRatingHistory.objects.all().order_by('-rating_index').first().rating_index + 1 if TeamRatingHistory.objects.all().exists() else 0
            end_season_rating_index = rating_index - 1
            # Save marker for season transition rating index
            TeamRatingHistory(team=Team.objects.get(short_name='NUL'), rating=0, match=match, rating_index=rating_index).save()

            for team in Team.objects.exclude(short_name='NUL'):
                try:
                    team_rating = TeamRating.objects.get(team=team)
                except ObjectDoesNotExist:
                    continue # Team doesn't exist yet
                if team != TeamRating.objects.filter(team__team_continuity_id=team.team_continuity_id).order_by('-rating_date').first().team:
                    continue # Old version of team

                prev = TeamRatingHistory.objects.filter(team=team).order_by('-rating_index').first()
                if prev.rating == team_rating.rating and prev.match.match_info == 'inter_season_reset':
                    TeamRatingHistory(team=team, match=match, rating_index=rating_index, rating=team_rating.rating).save()
                    continue # inactive team
                if prev.rating_index != end_season_rating_index:
                    TeamRatingHistory(team=team, match=match, rating_index=end_season_rating_index, rating=prev.rating).save()
                TeamRatingHistory(team=team, match=match, rating_index=rating_index, rating=team_rating.rating).save()

        else:
            # Normal match
            for team in [match.team1, match.team2]:
                team_rating = TeamRating.objects.get(team=team)
                rating_index = TeamRatingHistory.objects.filter(team=team).order_by('-rating_index').first().rating_index + 1
                TeamRatingHistory(team=team, match=match, rating_index=rating_index, rating=team_rating.rating).save()

    def _calculate_ratings(self):
        docstring = '''
Legend:
. : processed match
A : already processed
F : future match
N : no results yet
'''
        print(docstring)
        ordered_matches = Match.objects.all().order_by('start_timestamp')
        for match in ordered_matches.iterator():
            rating_changed = self._process_match(match)
            if rating_changed:
                self._update_rating_history(match, self.prev_match_region)
            self.prev_match_region = match.region
        print(f'\nProcessed {ordered_matches.count()} matches')

    def _clear_ratings(self):
        print('Clearing Team Ratings...')
        TeamRating.objects.all().delete()
        TeamRatingHistory.objects.all().delete()
        Match.objects.all().update(elo_processed=False)
        Prediction.objects.filter(user=self.elo_user).delete()

    def handle(self, *args, **options):
        if options['clear_ratings']:
            self._clear_ratings()
        self._calculate_ratings()
