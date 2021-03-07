from django.db import models
from colorfield.fields import ColorField

class Teams(models.Model):
    LEAGUE_REGIONS = [
        ('NA', 'North America'),
        ('EU', 'Europe'),
        ('KR', 'Korea'),
        ('CN', 'China'),
        ('INT', 'International')
    ]

    team_continuity_id = models.IntegerField()
    team_name = models.CharField(max_length=30)
    short_name = models.CharField(max_length=5)
    region = models.CharField(max_length=3,
        choices=LEAGUE_REGIONS)
    color1 = models.ColorField(default='#333333')
    color2 = models.ColorField(default='#333333')

