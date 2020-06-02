from django.db import models
from django.utils import timezone
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce

# Create your models here.


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

    def get_vote_cnt_by_mood_value(self):
        """
        get the number of times each mood value has been submitted for this option
        """
        vote_cnt_by_value = {}

        # returns list of (mood_value=-3, mood_value_cnt=17)
        query_result = PollOptionReply.objects. \
                filter(poll_option=self). \
                values('mood_value'). \
                annotate(
                    mood_value_cnt=Coalesce(Count('mood_value'), 0)
                    )

        # TODO read from cfg
        for i in range(-10, +10 + 1):
            vote_cnt_by_value[i] = 0

        for result_row in query_result:
            vote_cnt_by_value[result_row['mood_value']] = result_row['mood_value_cnt']

        print(vote_cnt_by_value)

        return vote_cnt_by_value

    def get_mood_sum(self):
        sum = PollOptionReply.objects.filter(poll_option=self).aggregate(Sum('mood_value'))['mood_value__sum']
        if sum:
            return sum
        return 0

    def get_mood_blame(self):
        sum = PollOptionReply.objects.filter(poll_option=self, mood_value__lt=0).aggregate(Sum('mood_value'))['mood_value__sum']
        if sum:
            return sum
        return 0

    def get_mood_praise(self):
        sum = PollOptionReply.objects.filter(poll_option=self, mood_value__gt=0).aggregate(Sum('mood_value'))['mood_value__sum']
        if sum:
            return sum
        return 0


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
