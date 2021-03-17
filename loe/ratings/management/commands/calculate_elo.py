import datetime
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from ratings.models import Team, TeamRating, Match
from ratings.management.LeagueOfElo.league_of_elo.elo.rating_system import Elo


class StaleRatingWarning(Exception):
    pass


class Command(BaseCommand):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.elo_model = Elo(K=30, score_mult=True)

    def _continuity_check(self, team, match_date):
        continuity_teams = Team.objects.filter(team_continuity_id=team.team_continuity_id)
        if not TeamRating.objects.filter(team__in=continuity_teams).exists():
            new_team = TeamRating(team=team, rating=1500, rating_date=match_date - datetime.timedelta(hours=1))
            new_team.save()
            print(f'\nCreated {new_team}')
        else:
            most_recent_rating = TeamRating.objects.filter(team__in=continuity_teams).order_by('-rating_date')[0]
            updated_rating, _ = TeamRating.objects.update_or_create(team=team,
                    defaults={'rating':most_recent_rating.rating, 'rating_date':most_recent_rating.rating_date})
            print(f'\nSet {updated_rating} from {most_recent_rating}')

    def _process_match(self, match):
        print('.', end='', flush=True)

        stale_rating_cutoff = match.match_datetime - datetime.timedelta(days=90)
        for team in [match.team1, match.team2]:
            try:
                rating = TeamRating.objects.get(team=team)
                if rating.rating_date < stale_rating_cutoff:
                    raise StaleRatingWarning
            except (ObjectDoesNotExist, StaleRatingWarning):
                self._continuity_check(team, match.match_datetime)
        t1_rating = TeamRating.objects.get(team=match.team1)
        t2_rating = TeamRating.objects.get(team=match.team2)

        if match.match_datetime <= t1_rating.rating_date:
            print('Team rating newer than match. Ignoring.')
            return
        if match.match_datetime > timezone.now():
            print('Match in future. Ignoring.')
            return
        if match.team1_score == 0 and match.team2_score == 0:
            print('Match results not recorded yet. Ignoring.')
            return

        t1_adj, t2_adj = self.elo_model.process_outcome(t1_rating.rating, t2_rating.rating, match.team1_score, match.team2_score)
        TeamRating.objects.filter(team=match.team1).update(rating=t1_rating.rating + t1_adj, rating_date=match.match_datetime)
        TeamRating.objects.filter(team=match.team2).update(rating=t2_rating.rating + t2_adj, rating_date=match.match_datetime)

    def _calculate_ratings(self):
        ordered_matches = Match.objects.all().order_by('match_datetime')
        for match in ordered_matches.iterator():
            self._process_match(match)

    def handle(self, *args, **options):
        self._calculate_ratings()
