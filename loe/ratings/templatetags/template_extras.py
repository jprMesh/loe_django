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
    context['match_started'] = match['start_timestamp'] < (timezone.now() + timedelta(hours=1))
    context['match_complete'] = match['elo_processed']

    prediction = Prediction.objects.filter(match__pk=match_pk, user__username=prediction_user)
    if prediction.exists():
        context['prediction_exists'] = True
        context['prediction'] = int(100.0 * prediction[0].predicted_t1_win_prob)
        if context['match_complete']:
            context['analyst_rating'] = prediction[0].analyst_rating

    context['model_pred'] = 50
    model_pred = Prediction.objects.filter(match__pk=match_pk, user__username='LeagueOfElo')
    if model_pred.exists():
        context['model_pred'] = int(100.0 * model_pred[0].predicted_t1_win_prob)

    return context


@register.inclusion_tag('user_stats.html')
def user_stats(active_user, page_user):
    context = dict()
    context['active_user'] = active_user
    context['page_user'] = page_user
    context['regions'] = ['Overall', 'NA', 'EU', 'KR', 'CN', 'INT']

    def get_stats(username, user_stats):
        '''Return Average Analyst Rating and Lifetime Analyst Rating'''
        user_stats['raw_ar'] = dict()
        user_stats['updown'] = dict()
        user_stats['num_pred'] = dict()

        avg_brier = Prediction.objects.filter(user__username=username).exclude(brier__isnull=True).values('user__username').annotate(avg_brier=Avg('brier'))
        num_predictions = Prediction.objects.filter(user__username=username).exclude(brier__isnull=True).count()
        if num_predictions == 0:
            return
        exp_mult = min(1.0, log10(num_predictions) / 3.0 )
        raw_ar = 100 - (100 * avg_brier[0]['avg_brier'])
        adjusted_ar = raw_ar * exp_mult
        user_stats['adjusted_ar'] = adjusted_ar

        user_stats['raw_ar']['Overall'] = f'{raw_ar:.2f}'
        user_stats['updown']['Overall'] = f'{100.0 * Prediction.objects.filter(user__username=username, brier__lt=0.25).count() / num_predictions:.1f}%'
        user_stats['num_pred']['Overall'] = num_predictions

        predictions = Prediction.objects.filter(user__username=username).exclude(brier__isnull=True)
        for region in context['regions'][1:]:
            region_predictions = predictions.filter(match__region=region)
            region_brier = region_predictions.values('user__username').annotate(avg_brier=Avg('brier'))
            user_stats[region] = dict()
            if region_brier.exists():
                user_stats['raw_ar'][region] = f'{100 - (100 * region_brier[0]["avg_brier"]):.2f}'
                user_stats['updown'][region] = f'{100.0 * region_predictions.filter(brier__lt=0.25).count() / region_predictions.count():.1f}%'
                user_stats['num_pred'][region] = region_predictions.count()

    context['loe_stats'] = dict()
    context['page_user_stats'] = dict()
    context['active_user_stats'] = dict()

    get_stats('LeagueOfElo', context['loe_stats'])
    get_stats(page_user, context['page_user_stats'])
    if active_user.is_authenticated:
        get_stats(active_user, context['active_user_stats'])

    return context


@register.inclusion_tag('team_ratings.html')
def team_ratings():
    context = dict()

    active_teams = (TeamRating.objects
            .filter(team__is_active=True, rating_date__gte=(timezone.now() - timedelta(days=150)))
            .exclude(team__region='INT', rating_date__lte=(timezone.now() - timedelta(days=28)))
            .exclude(team__short_name='NUL')
            .values('rating', 'team__team_name', 'team__short_name', 'team__region', 'team__color1')
            .order_by('-rating'))

    context['active_teams'] = active_teams
    return context


@register.inclusion_tag('history_chart.html')
def history_chart(time_span):
    return {'time_span': time_span}


@register.filter
def keyvalue(dict, key):
    return dict.get(key, 0)
