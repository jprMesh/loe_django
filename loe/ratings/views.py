import datetime
from math import log10
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
    active_teams = list(TeamRating.objects
            .filter(team__is_active=True, rating_date__gte=(timezone.now() - datetime.timedelta(days=150)))
            .exclude(team__region='INT')
            .values('rating', 'team__short_name', 'team__region')
            .order_by('-rating'))

    context = {
        'matches': upcoming_matches,
        'recent_matches': recent_matches,
        'teams': active_teams,
    }
    return render(request, 'ratings/index.html', context)


def leaderboard(request):
    brier_leaderboard = Prediction.objects.exclude(brier__isnull=True).values('user__username').annotate(avg_brier=Avg('brier')).order_by('avg_brier')
    for entry in brier_leaderboard:
        num_predictions = Prediction.objects.filter(user__username=entry['user__username']).exclude(brier__isnull=True).count()
        exp_mult = min(1.0, log10(num_predictions) / 3.0 )
        raw_ar = 100 - (200 * entry['avg_brier'])
        adjusted_ar = raw_ar * exp_mult
        entry['adjusted_ar'] = f'{adjusted_ar:.2f}'
        entry['raw_ar'] = f'{raw_ar:.2f}'
        entry['num_preds'] = num_predictions
    sorted_leaderboard = sorted(list(brier_leaderboard), key=lambda e: float(e['adjusted_ar']), reverse=True)

    context = {
        'leaderboard': sorted_leaderboard,
    }
    return render(request, 'ratings/leaderboard.html', context)


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
    return render(request, 'ratings/user_page.html', context)


# REST API Views

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
