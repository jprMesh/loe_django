# Generated by Django 3.1.7 on 2021-07-26 03:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ratings', '0013_teamratinghistory_rating_index'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='teamratinghistory',
            name='rating_date',
        ),
    ]
