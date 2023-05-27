from django.conf import settings

LAST_FEEDS_COUNT = getattr(settings, 'LAST_FEEDS_COUNT', 10)
