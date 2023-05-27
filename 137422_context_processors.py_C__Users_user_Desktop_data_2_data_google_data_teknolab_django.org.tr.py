from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.conf import settings


def current_site(request):
    return {'current_site': Site.objects.get_current()}


def current_page(request):
    path = request.path
    is_events = False
    is_blog = False
    is_profile = False
    is_home = False

    if path.startswith("/events/"):
        is_events = True
    elif path.startswith("/planet/"):
        is_blog = True
    elif path.startswith("/profile/"):
        is_profile = True
    else:
        is_home = True

    return {'is_home': is_home,
            'is_profile': is_profile,
            'is_blog': is_blog,
            'is_events': is_events}
