# Generated by Django 3.1.7 on 2021-03-27 03:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ratings', '0006_prediction_brier'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
