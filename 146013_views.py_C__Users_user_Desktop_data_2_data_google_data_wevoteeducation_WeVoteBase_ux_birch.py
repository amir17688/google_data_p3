# ux_birch/views.py
# Brought to you by We Vote. Be good.
# -*- coding: UTF-8 -*-

from django.shortcuts import render
from election_office_measure.models import BallotItemManager
from wevote_functions.models import get_voter_device_id, set_voter_device_id
from voter.models import VoterDeviceLinkManager, VoterManager


def my_ballot_view(request):
    generate_voter_device_id_if_needed = True
    voter_device_id = get_voter_device_id(request, generate_voter_device_id_if_needed)
    voter_id_found = False

    voter_device_link_manager = VoterDeviceLinkManager()
    results = voter_device_link_manager.retrieve_voter_device_link_from_voter_device_id(voter_device_id)
    if results['voter_device_link_found']:
        voter_device_link = results['voter_device_link']
        voter_id_found = True if voter_device_link.voter_id > 0 else False

    # If existing voter not found, create a new voter
    if not voter_id_found:
        # Create a new voter and return the id
        voter_manager = VoterManager()
        results = voter_manager.create_voter()

        if results['voter_created']:
            voter = results['voter']

            # Now save the voter_device_link
            results = voter_device_link_manager.save_new_voter_device_link(voter_device_id, voter.id)

            if results['voter_device_link_created']:
                voter_device_link = results['voter_device_link']
                voter_id_found = True if voter_device_link.voter_id > 0 else False

    if not voter_id_found:
        print "Voter ID not found, nor generated. This should not be possible. (Cookies may be turned off?)"
        ballot_item_list = []
    else:
        ballot_item_manager = BallotItemManager()
        results = ballot_item_manager.retrieve_all_ballot_items_for_voter(voter_device_link.voter_id)
        ballot_item_list = results['ballot_item_list']

    template_values = {
        'ballot_item_list':     ballot_item_list,
    }
    response = render(request, 'ux_birch/my_ballot.html', template_values)

    set_voter_device_id(request, response, voter_device_id)
    return response


def start_view(request):

    template_values = {

    }
    return render(request, 'ux_birch/start.html', template_values)


def ask_view(request, candidate_campaign_id):
    friends = []
    if hasattr(request, 'facebook'):
        friends = request.facebook.fetch_friends()

    template_values = {
        'friends': friends
    }

    return render(request, 'ux_birch/ask.html', template_values)
