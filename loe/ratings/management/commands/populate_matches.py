from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
import datetime
import pytz
from ratings.models import LEAGUE_REGIONS, Team, Match, TeamRating, Prediction, UserScore
from ratings.management.LeagueOfElo.league_of_elo.get_league_data import Leaguepedia_DB


IGNORE_TOURNAMENTS = [
    'Promotion',
    'Play-In',
    'Rift Rivals',
    'EU Face-Off',
    'Mid-Season Showdown',
    'IWCT']


class Command(BaseCommand):
    args = '<foo bar ...>'
    help = 'our help string comes here'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('start_year', type=int, nargs='?', default=2015, help='Year to start fetching data from')

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

    def _save_match(self, t1, t2, t1s, t2s, match_ts, tab, region):
        team1 = self._get_team(t1)
        team2 = self._get_team(t2)
        if not team1 or not team2:
            return
        date_format = '%Y-%m-%d %H:%M:%S'
        naive_match_ts = datetime.datetime.strptime(match_ts, date_format)
        tz_match_ts = pytz.utc.localize(naive_match_ts)

        # Return if exact record exists
        if Match.objects.filter(team1=team1, team2=team2,
                team1_score=t1s, team2_score=t2s,
                match_datetime=tz_match_ts, match_info=tab,
                region=region).exists():
            print('Record exists')
            return

        # Create or update record if new match or updated scores
        match, _ = Match.objects.update_or_create(
                team1=team1,
                team2=team2,
                match_datetime=tz_match_ts,
                match_info=tab,
                region=region,
                defaults={'team1_score': t1s, 'team2_score': t2s})
        print(match)

    def _load_matches(self, start_year):
        print('Loading match data from leaguepedia...')
        lpdb = Leaguepedia_DB()
        regions = [abbr for abbr, _ in LEAGUE_REGIONS]
        regions = ['NA']
        for region in regions:
            season_list = lpdb.getTournaments([region], start_year)
            season_list = list(filter(lambda x: all([t not in x for t in IGNORE_TOURNAMENTS]), season_list))

            for season in season_list:
                matches = lpdb.getSeasonResults(season)
                for match in matches:
                    self._save_match(*match, region=region)

    def handle(self, *args, **options):
        self._load_matches(options['start_year'])
