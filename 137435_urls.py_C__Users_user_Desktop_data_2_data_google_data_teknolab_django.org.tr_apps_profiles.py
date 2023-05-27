from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from apps.profiles.views import ProfileDetail
from apps.profiles.views import ProfileEdit
from apps.profiles.views import ProfileList

urlpatterns = patterns(
    '',

    url(r'^$', view=ProfileList.as_view(), name='profile_list'),
    url(r'^edit/$', view=ProfileEdit.as_view(), name='profile_form'),
    url(r'^(?P<username>[- \w]+)/$', view=ProfileDetail.as_view(),
        name='profile_detail')
)
