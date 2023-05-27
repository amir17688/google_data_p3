from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from apps.events.views import EventIndex
from apps.events.views import EventDetail

urlpatterns = patterns(
    '',

    url(r'^$', view=EventIndex.as_view(), name='event-index'),
    url(r'^(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/'
        r'(?P<slug>[-\w]+)/$', EventDetail.as_view(), name='event-detail')
)
