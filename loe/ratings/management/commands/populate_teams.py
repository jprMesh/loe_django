from collections import namedtuple
from pathlib import Path
from django.core.management.base import BaseCommand
from ratings.models import Team

COMMANDS_PATH = Path(__file__).resolve().parent
TEAMINFO = namedtuple('TeamInfo',
        ['region', 'continuity_id', 'short_name', 'team_name', 'color1', 'logo_img', 'color2'],
        defaults=['#868686', '', '#868686'])


class Command(BaseCommand):
    def _save_team(self, team_info):
        # Create if team doesn't exist yet
        team, created = Team.objects.update_or_create(region=team_info.region,
                team_continuity_id=team_info.continuity_id,
                team_name=team_info.team_name,
                short_name=team_info.short_name,
                defaults={
                    'color1': team_info.color1,
                    'color2': team_info.color2,
                    'logo_img': team_info.logo_img
                })
        print('New team: ' if created else 'Team exists: ', end='')
        print(team)

    def _load_teams(self):
        print('Loading teams from teams.csv...')
        with open(COMMANDS_PATH / 'teams.csv', 'r') as teams:
            for team in teams:
                if not team.strip(): continue
                team_info = TEAMINFO(*list(map(str.strip, team.split(','))))
                self._save_team(team_info)

    def handle(self, *args, **options):
        self._load_teams()
