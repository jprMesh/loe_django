from datetime import timedelta
from django import template
from django.utils import timezone
from django.contrib.auth import get_user_model
from ratings.models import Prediction, Match, Team, TeamRating

register = template.Library()


@register.inclusion_tag('prediction_tr.html')
def prediction_tr(match_pk, username):
    match = Match.objects.filter(pk=match_pk).values('pk',
        'team1__team_name', 'team1__short_name', 'team1__logo_img', 'team1_score',
        'team2__team_name', 'team2__short_name', 'team2__logo_img', 'team2_score',
        'best_of', 'region', 'start_timestamp', 'elo_processed').first()
    context = {'match': match}
    context['match_started'] = match['start_timestamp'] < (timezone.now() - timedelta(hours=1))
    context['match_complete'] = match['elo_processed']


    user = get_user_model().objects.filter(username=username)
    if user.exists():
        context['user'] = user[0]

    prediction = Prediction.objects.filter(match__pk=match_pk, user__username=username)
    if prediction.exists():
        context['prediction'] = int(100.0 * prediction[0].predicted_t1_win_prob)
        if context['match_complete']:
            context['analyst_rating'] = prediction[0].analyst_rating

    return context