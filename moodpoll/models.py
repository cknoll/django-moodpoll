from django.db import models
from django.utils import timezone

# Todo: the models need servere refactoring!


class Poll(models.Model):
    id = models.AutoField(primary_key=True)
    creation_datetime = models.DateTimeField(null=False, default=timezone.now,)
    title = models.CharField(max_length=200, null=True, blank=False,)
    description = models.CharField(max_length=500, null=True, blank=False,)
    key = models.PositiveIntegerField(null=False,)
    replies_hidden = models.BooleanField(null=False, default=False,)


class PollReply(models.Model):
    id = models.AutoField(primary_key=True)
    update_datetime = models.DateTimeField(null=False, default=timezone.now,)
    user_name = models.CharField(max_length=50, null=True, blank=False,)
    key = models.PositiveIntegerField(null=False,)
    poll = models.ForeignKey('Poll', on_delete=models.CASCADE, null=False,)


class PollOption(models.Model):
    id = models.AutoField(primary_key=True)
    text = models.CharField(max_length=200, null=True, blank=True,)
    poll = models.ForeignKey('Poll', on_delete=models.CASCADE, null=False,)


class PollOptionReply(models.Model):
    # the correct way to handle this would be to use both poll_option and poll_reply as primary keys.
    # however, django does not support this.
    id = models.AutoField(primary_key=True)

    class Meta:
        unique_together = [
            ['poll_reply', 'poll_option'],
        ]
    
    mood_value = models.IntegerField(null=False, default=0,)
    poll_option = models.ForeignKey('PollOption', on_delete=models.CASCADE, null=False,)
    poll_reply = models.ForeignKey('PollReply', on_delete=models.CASCADE, null=False,)
