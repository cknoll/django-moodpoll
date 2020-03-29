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
    title = models.CharField(max_length=200, null=True, blank=True)
    description = models.CharField(max_length=500, null=True)
    optionlist = models.TextField(max_length=5000)  # options are saved as str-represented list of strings
    # nbr_of_opts = models.IntegerField()


class MoodExpression(models.Model):
    # usernames should be specific only to one poll
    username = models.CharField(max_length=200, null=True)
    poll = models.ForeignKey(Poll, null=True, on_delete=models.SET_NULL)
    mood_values = models.TextField(max_length=1000)  # moods are saved as list of floats or ints
    datetime = models.DateTimeField(default=timezone.now, null=True)

    def __repr__(self):
        return "<MoodExpr [{}]: poll:{}, un:{}, {}>".format(self.pk, self.poll.pk, self.username, self.datetime)

