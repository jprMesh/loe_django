import datetime
from django.utils import timezone
from django.core.management.base import BaseCommand
from ratings.models import Team, TeamRating, Match
from ratings.management.LeagueOfElo.league_of_elo.elo.rating_system import Elo


class Command(BaseCommand):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.elo_model = Elo(K=30, score_mult=True)

    def _process_match(self, match):
        print('.', end='', flush=True)
        # TODO: need to add some logic for continuity
        t1_rating, _ = TeamRating.objects.get_or_create(team=match.team1,
                defaults={'rating': 1500, 'rating_date': match.match_datetime - datetime.timedelta(hours=1)})
        t2_rating, _ = TeamRating.objects.get_or_create(team=match.team2,
                defaults={'rating': 1500, 'rating_date': match.match_datetime - datetime.timedelta(hours=1)})

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
