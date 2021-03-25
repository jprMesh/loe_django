from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('user/<str:username>', views.user_page, name='user_page'),
    path('leaderboard', views.leaderboard, name='leaderboard'),
    path('upcoming', views.upcoming, name='upcoming'),
    path('hello', views.hello_world, name='hello')
]