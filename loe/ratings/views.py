import datetime
from django.http import HttpResponse
from django.template import loader
from django.db.models import Avg
from django.utils import timezone

from .models import Prediction, Match, Team


def index(request):
    return upcoming(request)


def upcoming(request):
    upcoming_matches = (Match.objects
            .filter(match_datetime__gte=timezone.now(), match_datetime__lte=timezone.now() + datetime.timedelta(days=14))
            .order_by('match_datetime')
            .values('pk', 'match_datetime', 'team1__short_name', 'team2__short_name', 'region'))
    template = loader.get_template('ratings/upcoming.html')
    context = {
        'matches': upcoming_matches
    }
    return HttpResponse(template.render(context, request))


def leaderboard(request):
    brier_leaderboard = Prediction.objects.all().values('user__username').annotate(brier=Avg('brier')).order_by('brier')[:20]
    template = loader.get_template('ratings/leaderboard.html')
    context = {
        'leaderboard': brier_leaderboard,
    }
    return HttpResponse(template.render(context, request))
