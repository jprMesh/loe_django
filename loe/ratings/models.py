from django.db import models
from django.conf import settings
from colorfield.fields import ColorField


class Teams(models.Model):
    LEAGUE_REGIONS = [
        ('NA', 'North America'),
        ('EU', 'Europe'),
        ('KR', 'Korea'),
        ('CN', 'China'),
        ('INT', 'International')
    ]

    # team_id pk
    team_continuity_id = models.IntegerField()
    team_name = models.CharField(max_length=30)
    short_name = models.CharField(max_length=5)
    region = models.CharField(max_length=3,
        choices=LEAGUE_REGIONS)
    color1 = ColorField(default='#333333')
    color2 = ColorField(default='#333333')
    logo_img = models.URLField()


class Matches(models.Model):
    # match_id pk
    team1 = models.ForeignKey(Teams, on_delete=models.CASCADE, related_name='+')
    team2 = models.ForeignKey(Teams, on_delete=models.CASCADE, related_name='+')
    team1_score = models.IntegerField()
    team2_score = models.IntegerField()
    match_datetime = models.DateTimeField()


class TeamRatings(models.Model):
    # teamrating_id pk
    team = models.ForeignKey(Teams, on_delete=models.CASCADE)
    rating_date = models.DateTimeField()
    rating = models.IntegerField()


class Predictions(models.Model):
    # prediction_id pk
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    match = models.ForeignKey(Matches, on_delete=models.CASCADE)
    predicted_t1_win_prob = models.IntegerField()


class UserScores(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    score = models.IntegerField()
    score_updated = models.DateTimeField(auto_now=True)
