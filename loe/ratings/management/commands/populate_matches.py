import datetime
import pytz
from math import ceil
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from ratings.models import LEAGUE_REGIONS, Team, Match, Prediction
from ratings.management.LeagueOfElo.league_of_elo.get_league_data import Leaguepedia_DB


IGNORE_TOURNAMENTS = [
    'Promotion',
    'Play-In',
    'Rift Rivals',
    'EU Face-Off',
    'Mid-Season Showdown 2020',
    'Streamathon',
    'IWCT']
SPRING_RESET = -1
SUMMER_RESET = -2


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_updated_matches = 0

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('start_year', type=int, nargs='?', default=2015, help='Year to start fetching data from')

    def _update_briers(self, match):
        if match.team1_score == 0 and match.team2_score == 0:
            return
        elif match.team1_score > match.team2_score:
            match_outcome = 1.0
        elif match.team1_score < match.team2_score:
            match_outcome = 0.0
        else:
            match_outcome = 0.5
        associated_predictions = match.prediction_set.all()
        for pred in associated_predictions:
            brier = (match_outcome - pred.predicted_t1_win_prob)**2
            Prediction.objects.filter(pk=pred.pk).update(brier=brier)

    def _get_team(self, team_name):
        try:
            team = Team.objects.get(team_name=team_name)
        except ObjectDoesNotExist:
            try:
                team = Team.objects.get(short_name=team_name)
            except ObjectDoesNotExist:
                print(f'UNKNOWN TEAM: {team_name}')
                return ''
        return team

    def _save_match(self, t1, t2, t1s, t2s, match_ts, bestof, tab, region):
        team1 = self._get_team(t1)
        team2 = self._get_team(t2)
        if not team1 or not team2:
            return
        date_format = '%Y-%m-%d %H:%M:%S'
        naive_match_ts = datetime.datetime.strptime(match_ts, date_format)
        tz_match_ts = pytz.utc.localize(naive_match_ts)

        t1s = 0 if not t1s else t1s
        t2s = 0 if not t2s else t2s
        bestof = 1 if not bestof else bestof

        # Return if exact record exists
        if Match.objects.filter(team1=team1, team2=team2,
                team1_score=t1s, team2_score=t2s,
                start_timestamp=tz_match_ts, best_of=bestof,
                match_info=tab, region=region).exists():
            print('X', end='', flush=True) # X for eXists
            return

        # Return if match has not completed yet
        if min(int(t1s), int(t2s)) > 0 and max(int(t1s), int(t2s)) < int(ceil(float(bestof)/2)):
            print('O', end='', flush=True) # O for Ongoing
            return

        # Create or update record if new match or updated scores
        match, _ = Match.objects.update_or_create(
                team1=team1,
                team2=team2,
                start_timestamp=tz_match_ts,
                match_info=tab,
                region=region,
                defaults={'team1_score': t1s, 'team2_score': t2s, 'best_of': bestof})
        self._update_briers(match)
        print(match)
        self.new_updated_matches += 1

    def _insert_season_reset(self, sdate, reset_type):
        reset_date = datetime.datetime.strptime(sdate, '%Y-%m-%d')
        tz_reset_date = pytz.utc.localize(reset_date) - datetime.timedelta(days=1)
        NullTeam = Team.objects.get(team_name='Null Team')
        _, created = Match.objects.get_or_create(
                team1=NullTeam, team2=NullTeam,
                start_timestamp=tz_reset_date,
                match_info='inter_season_reset',
                region='INT',
                best_of=0,
                team1_score=reset_type,
                team2_score=reset_type
            )
        print('\nSeason reset: {reset_type} on {sdate} -- {created}'.format(**{
            'reset_type': "spring" if reset_type == SPRING_RESET else "summer",
            'sdate': sdate,
            'created': "new record" if created else "exists"}))

    def _load_matches(self, start_year):
        print('Loading match data from leaguepedia...')
        lpdb = Leaguepedia_DB()
        regions = [abbr for abbr, _ in LEAGUE_REGIONS]
        season_list = []
        for region in regions:
            region_seasons = lpdb.getTournaments([region], start_year)
            season_list.extend([(sdate, season, region) for season, sdate in region_seasons])
        season_list = list(filter(lambda x: all([t not in x[1] for t in IGNORE_TOURNAMENTS]), season_list))
        season_list = sorted(season_list, key=lambda tup: tup[0])
        last_year = None
        summer_reset = False
        for sdate, season, region in season_list:
            year = sdate[:4]
            if year != last_year:
                self._insert_season_reset(sdate, SPRING_RESET)
                last_year = year
                summer_reset = False
            elif not summer_reset and 'Summer' in season:
                self._insert_season_reset(sdate, SUMMER_RESET)
                summer_reset = True
            print(f'\n{season}')
            matches = lpdb.getSeasonResults(season)
            for match in matches:
                self._save_match(*match, region=region)
        print(f'\n{self.new_updated_matches} new/updated matches')

    def handle(self, *args, **options):
        self._load_matches(options['start_year'])
