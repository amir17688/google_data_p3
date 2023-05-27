# wevotebase/views.py
# Brought to you by We Vote. Be good.
# -*- coding: UTF-8 -*-

from django.shortcuts import render

from politician.models import Politician
from election_office_measure.models import BallotItem

#
# def start_view(request):
#     ballot_item_list = BallotItem.objects.order_by('ballot_item_label')
#     template_values = {
#         'ballot_item_list': ballot_item_list,
#     }
#     return render(request, 'ux_oak/start.html', template_values)
