from django.db import models
from django.utils import timezone

# Create your models here.


class User(models.Model):
    """
    Very simple User (without login)
    """
    name = models.CharField(max_length=200)


class Poll(models.Model):
    creation_datetime = models.DateTimeField(default=timezone.now)
    title = models.CharField(max_length=200, null=True)
    description = models.CharField(max_length=500, null=True)
    optionlist = models.TextField(max_length=5000)  # options are saved as str-represended list of strings


class MoodExpression(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    poll = models.ForeignKey(Poll, null=True, on_delete=models.SET_NULL)
    mood_values = models.TextField(max_length=1000)  # moods are saved as list of floats

