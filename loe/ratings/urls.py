from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('submit_prediction', views.Predictions.as_view(), name='submit_prediction'),
    path('leaderboard', views.leaderboard, name='leaderboard'),
    path('stats', views.Stats.as_view(), name='stats'),
    path('about', views.about, name='about'),
    path('user/<str:prediction_user>', views.user_page, name='user_page'),
    path('user/<str:prediction_user>/accuracy_plot', views.AccuracyPlot.as_view()),
    path('match_table', views.MatchTable.as_view()),
    path('user/<str:prediction_user>/match_table', views.MatchTable.as_view()),
    path('history/team/<str:team>', views.EloHistory.as_view()),
    path('history/all_teams', views.EloHistoryAll.as_view()),
    path('history', views.history, name='history'),
]