# Generated by Django 3.0.6 on 2020-06-14 14:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('moodpoll', '0005_auto_20200601_1937'),
    ]

    operations = [
        migrations.AddField(
            model_name='poll',
            name='mood_value_max',
            field=models.IntegerField(default=2),
        ),
        migrations.AddField(
            model_name='poll',
            name='mood_value_min',
            field=models.IntegerField(default=-3),
        ),
    ]