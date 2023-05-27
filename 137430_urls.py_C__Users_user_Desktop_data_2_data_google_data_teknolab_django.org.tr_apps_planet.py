from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from apps.planet.views import PlanetIndex

urlpatterns = patterns(
    '',

    url(r'^$', view=PlanetIndex.as_view(), name='planet-index'),
)
