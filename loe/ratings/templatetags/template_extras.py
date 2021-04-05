from math import log10
from datetime import timedelta
from django import template
from django.utils import timezone
from django.db.models import Avg
from django.contrib.auth import get_user_model
from ratings.models import Prediction, Match, Team, TeamRating

register = template.Library()


@register.inclusion_tag('prediction_tr.html')
def prediction_tr(active_user, match_pk, prediction_user):
    context = dict()
    context['user'] = active_user
    context['prediction_user'] = prediction_user

    match = Match.objects.filter(pk=match_pk).values('pk',
        'team1__team_name', 'team1__short_name', 'team1__logo_img', 'team1_score',
        'team2__team_name', 'team2__short_name', 'team2__logo_img', 'team2_score',
        'best_of', 'region', 'start_timestamp', 'elo_processed').first()
    context['match'] = match
    context['match_started'] = match['start_timestamp'] < (timezone.now() - timedelta(hours=1))
    context['match_complete'] = match['elo_processed']

    prediction = Prediction.objects.filter(match__pk=match_pk, user__username=prediction_user)
    if prediction.exists():
        context['prediction'] = int(100.0 * prediction[0].predicted_t1_win_prob)
        if context['match_complete']:
            context['analyst_rating'] = prediction[0].analyst_rating

    return context


@register.inclusion_tag('user_stats.html')
def user_stats(active_user, page_user):
    context = dict()
    context['user'] = active_user
    context['page_user'] = page_user

    def get_lar(username):
        '''Return Average Analyst Rating and Lifetime Analyst Rating'''
        avg_brier = Prediction.objects.filter(user__username=username).exclude(brier__isnull=True).values('user__username').annotate(avg_brier=Avg('brier'))
        num_predictions = Prediction.objects.filter(user__username=username).exclude(brier__isnull=True).count()
        if num_predictions == 0:
            return None
        aar = 100 - (200 * avg_brier[0]['avg_brier'])
        exp_mult = min(10.0, 10 * log10(num_predictions) / 3.0)
        lar = aar * exp_mult
        return int(aar), int(lar)

    ars = get_lar(page_user)
    if ars:
        context['page_user_aar'] = ars[0]
        context['page_user_lar'] = ars[1]
    if active_user.is_authenticated:
        ars = get_lar(active_user)
        if ars:
            context['active_user_aar'] = ars[0]
            context['active_user_lar'] = ars[1]
    loe_aar, loe_lar = get_lar('LeagueOfElo')
    context['loe_aar'] = loe_aar
    context['loe_lar'] = loe_lar

    return context