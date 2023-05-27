from django.core.urlresolvers import reverse
from django.db import models
from utils import slugify


class Event(models.Model):
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    address = models.TextField(max_length=250, blank=True)
    start = models.DateTimeField(db_index=True)
    is_published = models.BooleanField(default=False)
    slug = models.SlugField(editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        url_args = (
            self.start.year, self.start.month, self.start.day, self.slug
        )

        return reverse('event-detail', args=url_args)

    def save(self, **kwargs):
        self.slug = slugify(self.title)

        return super(Event, self).save(**kwargs)

    class Meta:
        ordering = ('start',)
