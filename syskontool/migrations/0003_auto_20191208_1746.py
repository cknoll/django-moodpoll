# Generated by Django 3.0 on 2019-12-08 17:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('syskontool', '0002_auto_20191207_1757'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='moodexpression',
            name='user',
        ),
        migrations.AddField(
            model_name='moodexpression',
            name='username',
            field=models.CharField(max_length=200, null=True),
        ),
    ]
