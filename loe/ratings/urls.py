from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('user/<str:username>', views.user_page, name='user_page'),
    path('leaderboard', views.leaderboard, name='leaderboard'),
    path('upcoming', views.upcoming, name='upcoming'),
    path('submit_prediction', views.Predictions.as_view(), name='submit_prediction'),
    path('upcoming_matches', views.UpcomingMatches.as_view(), name='upcoming_matches'),
]