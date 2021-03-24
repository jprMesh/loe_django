from django.db import models
from django.conf import settings
from colorfield.fields import ColorField


LEAGUE_REGIONS = [
    ('NA', 'North America'),
    ('EU', 'Europe'),
    ('KR', 'Korea'),
    ('CN', 'China'),
    ('INT', 'International')
]


class Team(models.Model):
    # team_id pk
    team_continuity_id = models.IntegerField()
    team_name = models.CharField(max_length=30)
    short_name = models.CharField(max_length=5)
    region = models.CharField(max_length=3,
        choices=LEAGUE_REGIONS)
    color1 = ColorField()
    color2 = ColorField()
    logo_img = models.URLField()

    def __str__(self):
        return self.team_name

    def __repr__(self):
        return f'<{self.pk}> {self.region} {self.team_continuity_id} -- {self.short_name} {self.team_name:<25}\t{self.color1} {self.color2}  {self.logo_img}'


class Match(models.Model):
    # match_id pk
    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='side1_match')
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='side2_match')
    team1_score = models.IntegerField()
    team2_score = models.IntegerField()
    match_datetime = models.DateTimeField()
    match_info = models.CharField(max_length=20)
    region = models.CharField(max_length=3,
        choices=LEAGUE_REGIONS)
    elo_processed = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.match_datetime} {self.region:3}\t{self.team1.short_name} vs {self.team2.short_name}\t{self.team1_score}:{self.team2_score}\t{self.match_info}'


class TeamRating(models.Model):
    # teamrating_id pk
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    rating_date = models.DateTimeField()
    rating = models.FloatField()

    def __str__(self):
        return f'{self.rating:.2f} -- {self.team}: {self.rating_date}'


class Prediction(models.Model):
    # prediction_id pk
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    predicted_t1_win_prob = models.FloatField()
    brier = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f'{self.user}: {self.predicted_t1_win_prob} :: {self.brier} -- {self.match}'

    @property
    def analyst_rating(self):
        return 100 - int(200 * self.brier)


class UserScore(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    score = models.FloatField()
    score_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user}: {str(self.score)} -- {str(self.score_updated)}'
