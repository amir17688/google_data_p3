from django.views.generic import ListView
from apps.planet.models import Feed
from apps.planet.models import FeedItem


class PlanetIndex(ListView):
    template_name = 'planet/index.html'
    queryset = FeedItem.objects.filter(feed__is_active=True)[:100]

    def get_context_data(self, **kwargs):
        context_data = super(PlanetIndex, self).get_context_data(**kwargs)
        context_data.update({
            'author_list': Feed.objects.filter(is_active=True)
        })

        return context_data
