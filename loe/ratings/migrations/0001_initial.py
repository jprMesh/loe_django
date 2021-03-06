# Generated by Django 3.1.7 on 2021-03-08 04:34

import colorfield.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('team1_score', models.IntegerField()),
                ('team2_score', models.IntegerField()),
                ('match_datetime', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('team_continuity_id', models.IntegerField()),
                ('team_name', models.CharField(max_length=30)),
                ('short_name', models.CharField(max_length=5)),
                ('region', models.CharField(choices=[('NA', 'North America'), ('EU', 'Europe'), ('KR', 'Korea'), ('CN', 'China'), ('INT', 'International')], max_length=3)),
                ('color1', colorfield.fields.ColorField(default='#FFFFFF', max_length=18)),
                ('color2', colorfield.fields.ColorField(default='#FFFFFF', max_length=18)),
                ('logo_img', models.URLField()),
            ],
        ),
        migrations.CreateModel(
            name='UserScore',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField()),
                ('score_updated', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TeamRating',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating_date', models.DateTimeField()),
                ('rating', models.IntegerField()),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ratings.team')),
            ],
        ),
        migrations.CreateModel(
            name='Prediction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('predicted_t1_win_prob', models.IntegerField()),
                ('match', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ratings.match')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='match',
            name='team1',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='side1_match', to='ratings.team'),
        ),
        migrations.AddField(
            model_name='match',
            name='team2',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='side2_match', to='ratings.team'),
        ),
    ]
