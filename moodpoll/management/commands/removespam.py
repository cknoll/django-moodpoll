
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from django.utils import timezone
from moodpoll import models


model_blacklist = ["contenttypes*", "sessions*", r"admin\.logentry",
                   r"auth\.permission", r"captcha\.captchastore"]


class Command(BaseCommand):
    """
    Filter out spam entries or irrelevant polls
    """
    help = 'Filter out spam entries or irrelevant polls'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        from ipydex import IPS, activate_ips_on_exception
        activate_ips_on_exception()

        annotated_polls = models.Poll.objects.annotate(Count('pollreply'))
        past_time = timezone.now() - timezone.timedelta(hours=3)

        # this is instance-specific but it does not harm
        spam_begin_time = timezone.datetime(2021, 6, 13, tzinfo=timezone.get_current_timezone())

        spam_polls = annotated_polls.filter(pollreply__count__lte=0,
                                            creation_datetime__lt=past_time,
                                            creation_datetime__gt=spam_begin_time
                                            )

        res = spam_polls.delete()

        msg = f"{self.style.SUCCESS('Done.')} {res[0]} objects deleted."
        self.stdout.write(msg)
