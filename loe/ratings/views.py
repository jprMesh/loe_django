from django.http import HttpResponse
from django.template import loader
from django.db.models import Avg

from .models import Prediction


def index(request):
    return HttpResponse("Nothing here yet. Go to /leaderboard")


def leaderboard(request):
    brier_leaderboard = Prediction.objects.all().values('user__username').annotate(brier=Avg('brier')).order_by('brier')[:20]
    template = loader.get_template('ratings/leaderboard.html')
    context = {
        'leaderboard': brier_leaderboard,
    }
    return HttpResponse(template.render(context, request))
