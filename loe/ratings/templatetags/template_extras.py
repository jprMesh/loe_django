from django import template
from django.contrib.auth import get_user_model
from ratings.models import Prediction, Match, Team, TeamRating

register = template.Library()


@register.inclusion_tag('prediction_tr.html')
def prediction_tr(match_pk, username):
    match = Match.objects.filter(pk=match_pk).values('pk', 'team1__team_name', 'team1__short_name', 'team2__team_name', 'team2__short_name', 'best_of', 'region')
    context = {'match': match[0]}

    user = get_user_model().objects.filter(username=username)
    if user.exists():
        context['user'] = user[0]

    prediction = Prediction.objects.filter(match__pk=match_pk, user__username=username).values('predicted_t1_win_prob')
    if prediction.exists():
        context['prediction'] = int(100.0 * prediction[0]['predicted_t1_win_prob'])

    return context