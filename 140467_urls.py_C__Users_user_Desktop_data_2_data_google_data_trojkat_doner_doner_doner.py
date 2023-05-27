from django.conf.urls import patterns, include, url
from django.views.generic.base import RedirectView
from django.contrib import admin

from doner.views import UserChangePassword, UserEdit, UserDetails

admin.autodiscover()


urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),

    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}, name='login'),
    url(r'^logout/$', 'doner.views.logout_view', name='logout'),

    url(r'^users/(?P<slug>[-.\w]+)/change-password/$', UserChangePassword.as_view(), name='change-password'),
    url(r'^users/(?P<slug>[-.\w]+)/edit/$', UserEdit.as_view(), name='user-edit'),
    url(r'^users/(?P<slug>[-.\w]+)/$', UserDetails.as_view(), name='user'),

    url(r'', include('project.urls')),
)
