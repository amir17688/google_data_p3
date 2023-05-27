# import_export_theunitedstatesio/views.py
# Brought to you by We Vote. Be good.
# -*- coding: UTF-8 -*-

from django.shortcuts import redirect, render
from django.views import generic

from .models import TheUnitedStatesIoLegislatorCurrent
from .controllers import import_legislators_current_csv


def import_theunitedstatesio_from_csv_view(request):
    """
    Take data from csv file and store in the local TheUnitedStatesIo database (TheUnitedStatesIoLegislatorCurrent)
    Then display to the import template from the database
    """
    # If person isn't signed in, we don't want to let them visit this page yet
    if not request.user.is_authenticated():
        return redirect('/admin')

    import_legislators_current_csv()

    template_values = {
        'legislator_list': TheUnitedStatesIoLegislatorCurrent.objects.order_by('last_name'),
    }
    return render(request, 'import_export_theunitedstatesio/import.html', template_values)


# TODO Upgrade to use render like above
class LegislatorCurrentDetailView(generic.DetailView):
    model = TheUnitedStatesIoLegislatorCurrent
    template_name = 'import_export_theunitedstatesio/legislatorcurrent_detail.html'

    def get_queryset(self):
        """

        """
        return TheUnitedStatesIoLegislatorCurrent.objects
