from django.conf.urls import url
from django.urls import path
from django.views.generic.base import RedirectView

from .views.new_poll import NewPollView
from .views.show_poll import ShowPollView
from .views.poll_result import PollResultView
from .views.poll_reply_cancel import PollReplyCancelView
from . import views_monolith as views

urlpatterns = [
  url(r'^$', NewPollView.as_view(), name='landing-page'),
  path('new', NewPollView.as_view(), name='new_poll'),
  path('show/<int:pk>/<int:key>', ShowPollView.as_view(), name='show_poll'),
  path('res/<int:pk>/<int:key>', PollResultView.as_view(), name='poll_result'),
  path('cancel/<int:pk>/<int:key>', PollReplyCancelView.as_view(), name='reply_cancel'),

  path('imprint', views.view_simple_page, name='imprint-page', kwargs={"pagetype": "imprint"}),
  path('privacy', views.view_simple_page, name='privacy-page', kwargs={"pagetype": "privacy"}),
  path('contact', views.view_simple_page, name='contact-page', kwargs={"pagetype": "contact"}),
  path('about', views.view_simple_page, name='about-page', kwargs={"pagetype": "about"}),

  # views with @login_required will use this:
  path('accounts/login/',  RedirectView.as_view(url="/admin/login/"), name='login_redirect'),

]
