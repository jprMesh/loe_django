from django.db.models import Avg
from django.core.management.base import BaseCommand
from ratings.models import Prediction


class Command(BaseCommand):
    def _print_briers(self):
        brier_leaderboard = Prediction.objects.all().values('user__username').annotate(brier=Avg('brier')).order_by('brier')
        for user in brier_leaderboard:
            print(f"{user['user__username']:<16}  {user['brier']}")

    def handle(self, *args, **options):
        self._print_briers()
