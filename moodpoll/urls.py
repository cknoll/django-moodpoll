from django.conf.urls import url
from django.urls import path

from . import views

urlpatterns = [
  url(r'^$', views.index, name='index'),
  path('new', views.ViewCreatePoll.as_view(), name='new_poll'),
  path('show/<int:pk>', views.ViewPoll.as_view(), name='show_poll'),
  path('res/<int:pk>', views.ViewPollResult.as_view(), name='poll_result'),
]
