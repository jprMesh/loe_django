from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('leaderboard', views.leaderboard, name='leaderboard'),
    path('stats', views.Stats.as_view(), name='stats'),
    path('about', views.about, name='about'),
    path('user/<str:prediction_user>', views.user_page, name='user_page'),
    path('submit_prediction', views.Predictions.as_view(), name='submit_prediction'),
    path('match_table', views.MatchTable.as_view(), name='match_table'),
]