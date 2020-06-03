from django.contrib import admin

from .models import Poll, PollOption, PollReply, PollOptionReply

# Register your models here.

admin.site.register(Poll)
admin.site.register(PollOption)
admin.site.register(PollReply)
admin.site.register(PollOptionReply)
