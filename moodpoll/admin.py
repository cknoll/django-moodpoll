from django.contrib import admin

from .models import User, Poll, MoodExpression

# Register your models here.

admin.site.register(User)
admin.site.register(Poll)
admin.site.register(MoodExpression)
