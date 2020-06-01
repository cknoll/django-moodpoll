from django.conf.urls import url
from django.urls import path
from django.views.generic.base import RedirectView

from .views.new_poll import NewPollView
from .views.show_poll import ShowPollView
from . import views_monolith as views

urlpatterns = [
  url(r'^$', views.view_simple_page, name='landing-page', kwargs={"pagetype": "landing"}),
  path('new', NewPollView.as_view(), name='new_poll'),
  path('show/<int:pk>/<int:key>', ShowPollView.as_view(), name='show_poll'),
  path('res/<int:pk>/<int:key>', views.ViewPollResult.as_view(), name='poll_result'),
  path('poll_eval/<int:pk>', views.ViewPollEvaluation.as_view(), name='poll_eval'),
  path('backup', views.view_do_backup, name='do_backup'),

  path('imprint', views.view_simple_page, name='imprint-page', kwargs={"pagetype": "imprint"}),
  path('privacy', views.view_simple_page, name='privacy-page', kwargs={"pagetype": "privacy"}),
  path('contact', views.view_simple_page, name='contact-page', kwargs={"pagetype": "contact"}),
  path('about', views.view_simple_page, name='about-page', kwargs={"pagetype": "about"}),

  # views with @login_required will use this:
  path('accounts/login/',  RedirectView.as_view(url="/admin/login/"), name='login_redirect'),

]
