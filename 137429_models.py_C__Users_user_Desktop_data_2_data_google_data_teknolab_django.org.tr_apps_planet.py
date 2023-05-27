from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Feed(models.Model):
    title = models.CharField(_("Title"), max_length=250)
    feed_url = models.URLField(_("Feed URL"), unique=True, verify_exists=False)
    site_url = models.URLField(_("Site URL"), verify_exists=False)
    is_active = models.BooleanField(_("Is Active?"), default=True)
    owner = models.OneToOneField(User, blank=True, null=True)

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _("Feed")
        verbose_name_plural = _("Feeds")


class FeedItem(models.Model):
    feed = models.ForeignKey(
        Feed, verbose_name=_("Feed"), related_name='feeditems')
    title = models.CharField(_("Title"), max_length=250)
    link = models.URLField(_("Link"), blank=True)
    content = models.TextField(_("Content"))
    published_at = models.DateTimeField(_("Published At"))

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ('-published_at',)
        verbose_name = _("Feed Item")
        verbose_name_plural = _("Feed Items")
