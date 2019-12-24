from django.conf.urls import url
from django.urls import path
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
  url(r'^$', views.view_simple_page, name='landing-page', kwargs={"pagetype": "landing"}),
  path('new', views.ViewCreatePoll.as_view(), name='new_poll'),
  path('show/<int:pk>', views.ViewPoll.as_view(), name='show_poll'),
  path('res/<int:pk>', views.ViewPollResult.as_view(), name='poll_result'),
  path('backup', views.view_do_backup, name='do_backup'),

  path('imprint', views.view_simple_page, name='imprint-page', kwargs={"pagetype": "imprint"}),
  path('privacy', views.view_simple_page, name='privacy-page', kwargs={"pagetype": "privacy"}),
  path('contact', views.view_simple_page, name='contact-page', kwargs={"pagetype": "contact"}),
  path('about', views.view_simple_page, name='about-page', kwargs={"pagetype": "about"}),

  # views with @login_required will use this:
  path('accounts/login/',  RedirectView.as_view(url="/admin/login/"), name='login_redirect'),

]
