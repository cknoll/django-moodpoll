from django.db import models
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.db.models.functions import Coalesce
from django.conf import settings
from random import randrange

# Todo: the models need servere refactoring!


def get_rdm_key():
    # note: copied from django doc
    return randrange(1, 2147483647)


class BaseModel(models.Model):
    """
    prevent PyCharm from complaining on .objects-attribute
    source: https://stackoverflow.com/a/56845199/333403
    """
    objects = models.Manager()

    class Meta:
        abstract = True


class Poll(BaseModel):
    id = models.AutoField(primary_key=True)
    creation_datetime = models.DateTimeField(null=False, default=timezone.now,)
    title = models.CharField(max_length=200, null=True, blank=False,)
    description = models.CharField(max_length=500, null=True, blank=False,)
    key = models.PositiveIntegerField(null=False, default=get_rdm_key,)
    replies_hidden = models.BooleanField(null=False, default=False,)

    # configuration values
    mood_value_min = models.IntegerField(null=False, default=settings.MOOD_VALUE_MIN)
    mood_value_max = models.IntegerField(null=False, default=settings.MOOD_VALUE_MAX)
    deadline = models.DateTimeField(null=True, default=None)
    require_name = models.BooleanField(null=False, default=False,)

    # if True: The name of those users which have voted with the most negative value
    # (regarded as veto) on at least one option will be published on the result view of the poll
    expose_veto_names = models.BooleanField(null=False, default=False,)

    def is_vote_possible(self):
        if self.deadline and self.deadline < timezone.now():
            return False
        return True

    def is_result_visible(self):
        if self.deadline and self.deadline >= timezone.now():
            return False
        return True


class PollReply(BaseModel):
    id = models.AutoField(primary_key=True)
    update_datetime = models.DateTimeField(null=False, default=timezone.now,)
    user_name = models.CharField(max_length=50, null=True, blank=False,)
    key = models.PositiveIntegerField(null=False,default=get_rdm_key,)
    poll = models.ForeignKey('Poll', on_delete=models.CASCADE, null=False,)

    def get_cancel_time_left(self):
        # can be cancelled if < 120s since submission
        delta = timezone.now() - self.update_datetime
        return 120 - delta.seconds

    def is_cancelable(self):
        if self.get_cancel_time_left() > 0:
            return self.poll.is_vote_possible()
        return False

    def cancel(self):
        if not self.is_cancelable():
            return

        self.delete()


class PollOption(BaseModel):
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

        for i in range(self.poll.mood_value_min, self.poll.mood_value_max + 1):
            vote_cnt_by_value[i] = 0

        for result_row in query_result:
            vote_cnt_by_value[result_row['mood_value']] = result_row['mood_value_cnt']

        return vote_cnt_by_value

    def get_mood_sum(self):
        sum = PollOptionReply.objects.filter(poll_option=self).aggregate(Sum('mood_value'))['mood_value__sum']
        if sum:
            return sum
        return 0

    def get_minimum_vote_cnt(self):
        # note: can't be None as the other options because aggregation does not happen on DB level
        return PollOptionReply.objects.filter(poll_option=self, mood_value=self.poll.mood_value_min).count()

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


class PollOptionReply(BaseModel):
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
