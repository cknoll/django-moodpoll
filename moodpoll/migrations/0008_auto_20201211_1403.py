# Generated by Django 3.1.4 on 2020-12-11 14:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('moodpoll', '0007_auto_20200910_1057'),
    ]

    operations = [
        migrations.AddField(
            model_name='poll',
            name='deadline',
            field=models.DateTimeField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name='poll',
            name='mood_value_max',
            field=models.IntegerField(default=10),
        ),
        migrations.AlterField(
            model_name='poll',
            name='mood_value_min',
            field=models.IntegerField(default=-10),
        ),
    ]
