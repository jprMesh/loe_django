import datetime
from django.http import HttpResponse
from django.template import loader
from django.db.models import Avg, Max
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Prediction, Match, Team, TeamRating
from .serializers import PredictionSerializer


def index(request):
    upcoming_matches = list(Match.objects
            .filter(start_timestamp__gte=timezone.now(), start_timestamp__lte=timezone.now() + datetime.timedelta(days=14))
            .order_by('start_timestamp'))
    recent_matches = list(Match.objects
            .filter(start_timestamp__lte=timezone.now())
            .order_by('-start_timestamp'))[:15]
    er = EloRanking()
    active_teams = er.get(request)

    template = loader.get_template('ratings/index.html')
    context = {
        'matches': upcoming_matches,
        'recent_matches': recent_matches,
        'teams': active_teams,
    }
    return HttpResponse(template.render(context, request))


def leaderboard(request):
    brier_leaderboard = Prediction.objects.exclude(brier__isnull=True).values('user__username').annotate(brier=Avg('brier')).order_by('brier')[:30]
    for entry in brier_leaderboard:
        entry['analyst_rating'] = int(100 - (200 * entry['brier']))
        entry['brier'] = f"{entry['brier']:.4f}"
    template = loader.get_template('ratings/leaderboard.html')
    context = {
        'leaderboard': brier_leaderboard,
    }
    return HttpResponse(template.render(context, request))


def about(request):
    return render(request, 'ratings/about.html')


def user_page(request, prediction_user):
    user_predictions = Prediction.objects.filter(user__username=prediction_user)
    past_matches = (user_predictions.filter(match__start_timestamp__lte=timezone.now())
            .values('match__pk').order_by('-match__start_timestamp'))[:50]
    future_matches = (user_predictions.filter(match__start_timestamp__gte=timezone.now())
            .values('match__pk').order_by('-match__start_timestamp'))
    context = {
        'prediction_user': prediction_user,
        'past_matches': past_matches,
        'future_matches': future_matches
    }
    template = loader.get_template('ratings/user_page.html')
    return HttpResponse(template.render(context, request))


# REST API Views

class EloRanking(APIView):
    def get(self, request):
        active_teams = (TeamRating.objects
                .filter(team__is_active=True, rating_date__gte=(timezone.now() - datetime.timedelta(days=90)))
                .exclude(team__region='INT')
                .values('rating', 'team__short_name', 'team__region')
                .order_by('-rating'))
        for team in active_teams:
            team['rating'] = int(team['rating'])
        return active_teams


class Predictions(APIView):
    def post(self, request):
        def validate(request):
            if not request.user.is_authenticated or request.user.username != request.data['username']:
                return False, 'invalid_user'
            match = Match.objects.filter(pk=str(request.data['match']))
            if not match.exists():
                return False, 'invalid_match'
            if timezone.now() > match[0].start_timestamp - datetime.timedelta(hours=1):
                return False, 'match_started'
            if not 0 <= int(request.data['predicted_t1_win_prob']) <= 100:
                return False, 'invalid_prediction'
            return True, None

        valid, reason = validate(request)
        if not valid:
            return Response(reason, status=status.HTTP_400_BAD_REQUEST)

        match = Match.objects.get(pk=str(request.data['match']))
        user_prediction = float(request.data['predicted_t1_win_prob']) / 100.0
        pred, _ = Prediction.objects.update_or_create(user=request.user, match=match, defaults={'predicted_t1_win_prob': user_prediction})
        print(pred)
        return Response(status=status.HTTP_200_OK)
