# import_export_voting_info_project/views.py
# Brought to you by We Vote. Be good.
# https://github.com/votinginfoproject
# -*- coding: UTF-8 -*-

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from .controllers import import_voting_info_project_from_xml


def import_voting_info_project_from_xml_view(request):
    """
    Take data from Test XML file and store in the local Voting Info Project database
    """
    # If person isn't signed in, we don't want to let them visit this page yet
    if not request.user.is_authenticated():
        return redirect('/admin')

    import_voting_info_project_from_xml()

    messages.add_message(request, messages.INFO, 'XML sample data imported.')

    return HttpResponseRedirect(reverse('import_export:import_export_index', args=()))
