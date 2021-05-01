import datetime
import logging
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


SPRING_RESET = -1
SUMMER_RESET = -2
logger = logging.getLogger(__name__)


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
    brier_leaderboard = Prediction.objects.values('user__username').annotate(avg_brier=Avg('brier')).order_by('avg_brier')
    for entry in brier_leaderboard:
        entry['user_id'] = get_user_model().objects.get(username=entry['user__username']).pk
        num_predictions = Prediction.objects.filter(user__username=entry['user__username']).exclude(brier__isnull=True).count()
        entry['num_preds'] = num_predictions
        if num_predictions == 0:
            entry['adjusted_ar'] = '0.00'
            entry['up_down'] = '0.0%'
            continue
        exp_mult = min(1.0, log10(num_predictions) / 3.0 )
        raw_ar = 100 - (100 * entry['avg_brier'])
        adjusted_ar = raw_ar * exp_mult
        entry['adjusted_ar'] = f'{adjusted_ar:.2f}'
        up_down_correct = Prediction.objects.filter(user__username=entry['user__username'], brier__lt=0.25).count()
        entry['up_down'] = f'{100.0 * up_down_correct / num_predictions:.1f}%'

    def get_seasons():
        seasons = []
        resets = Match.objects.filter(match_info='inter_season_reset', start_timestamp__lte=timezone.now()).order_by('-start_timestamp')
        season_intl_tournament = Match.objects.filter(
                region='INT',
                start_timestamp__gte=resets.first().start_timestamp,
                start_timestamp__lte=timezone.now() + datetime.timedelta(days=14)
                ).exclude(match_info='inter_season_reset').exists()
        for reset_ts in resets:
            year = reset_ts.start_timestamp.year
            season, intl_tournament = ('Spring', 'MSI') if reset_ts.start_timestamp.month < 3 else ('Summer', 'Worlds')
            season_name = f'{year} {season}'
            tournament_name = f'{year} {intl_tournament}'
            if season_intl_tournament:
                seasons.append(tournament_name)
            seasons.append(season_name)
            season_intl_tournament = True
        return seasons

    context = {
        'leaderboard': brier_leaderboard,
        'seasons': get_seasons(),
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
        logger.debug(f'Prediction submitted: {pred}')
        return Response(status=status.HTTP_200_OK)


class Stats(APIView):
    def get(self, request):
        season = request.GET.get('season', '')[:20]
        if not season:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        year, tournament = season.split(' ', 1)
        if tournament in ('Spring', 'MSI'):
            reset_start = Match.objects.filter(match_info='inter_season_reset', start_timestamp__year=int(year), team1_score=SPRING_RESET)[0].start_timestamp
            try:
                reset_end = Match.objects.filter(match_info='inter_season_reset', start_timestamp__year=int(year), team1_score=SUMMER_RESET)[0].start_timestamp
            except Exception as e:
                reset_end = timezone.now() + datetime.timedelta(days=180)
        elif tournament in ('Summer', 'Worlds'):
            reset_start = Match.objects.filter(match_info='inter_season_reset', start_timestamp__year=int(year), team1_score=SUMMER_RESET)[0].start_timestamp
            try:
                reset_end = Match.objects.filter(match_info='inter_season_reset', start_timestamp__year=int(year)+1, team1_score=SPRING_RESET)[0].start_timestamp
            except Exception as e:
                reset_end = timezone.now() + datetime.timedelta(days=180)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        season_preds = Prediction.objects.filter(match__start_timestamp__gte=reset_start, match__start_timestamp__lte=reset_end)
        if tournament in ('MSI', 'Worlds'):
            season_preds = season_preds.filter(match__region='INT')
        else:
            season_preds = season_preds.exclude(match__region='INT')
        users_w_scores = season_preds.exclude(brier__isnull=True).values('user__pk').annotate(avg_brier=Avg('brier')).order_by('avg_brier')
        for entry in users_w_scores:
            num_predictions = season_preds.filter(user__pk=entry['user__pk']).exclude(brier__isnull=True).count()
            raw_ar = 100 - (100 * entry['avg_brier'])
            del entry['avg_brier']
            entry['raw_ar'] = f'{raw_ar:.2f}'
            up_down_correct = season_preds.filter(user__pk=entry['user__pk'], brier__lt=0.25).count()
            entry['up_down'] = f'{100.0 * up_down_correct / num_predictions:.1f}%'

            all_user_season_preds = season_preds.filter(user__pk=entry['user__pk']).exclude(brier__isnull=True)
            score = 0
            for pred in all_user_season_preds:
                score += (100 - (100 * pred.brier))
            entry['score'] = f'{score:.0f}'

        return Response(data=users_w_scores, status=status.HTTP_200_OK)
