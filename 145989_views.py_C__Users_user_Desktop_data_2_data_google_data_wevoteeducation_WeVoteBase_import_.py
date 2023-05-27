# import_export/views.py
# Brought to you by We Vote. Be good.
# -*- coding: UTF-8 -*-

from django.contrib import messages
from django.contrib.messages import get_messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from election_office_measure.models import CandidateCampaign, CandidateCampaignManager, ContestMeasure, ContestOffice, \
    MeasureCampaign
from exception.models import handle_record_not_saved_exception
from .controllers import transfer_google_civic_voterinfo_cached_data_to_wevote_tables
from .models import transfer_theunitedstatesio_cached_data_to_wevote_tables, import_we_vote_organizations_from_json, \
    import_we_vote_candidate_campaigns_from_json, import_we_vote_positions_from_json
from import_export_maplight.models import MapLightCandidate
from .serializers import CandidateCampaignSerializer, OrganizationSerializer, PositionSerializer
from organization.models import Organization
from politician.models import Politician
from position.models import PositionEntered
from rest_framework.views import APIView
from rest_framework.response import Response
import wevote_functions.admin
from wevote_functions.models import value_exists


logger = wevote_functions.admin.get_logger(__name__)


# http://localhost:8000/import_export/
def import_export_index(request):
    """
    Provide an index of import/export actions (for We Vote data maintenance)
    """
    messages_on_stage = get_messages(request)

    template_values = {
        'messages_on_stage':    messages_on_stage,
    }
    return render(request, 'import_export/index.html', template_values)


# http://localhost:8000/import_export/transfer_from_google_civic/
def import_export_transfer_google_civic_to_local_tables_view(request):
    """
    Take data from the local TheUnitedStatesIo database (TheUnitedStatesIoLegislatorCurrent)
    and transfer it to the We Vote data structures
    """
    # If person isn't signed in, we don't want to let them visit this page yet
    if not request.user.is_authenticated():
        return redirect('/admin')

    transfer_google_civic_voterinfo_cached_data_to_wevote_tables()

    template_values = {
        'politician_list': Politician.objects.order_by('last_name'),
    }
    return render(request, 'import_export/transfer_from_google_civic.html', template_values)


# http://localhost:8000/import_export/transfer_from_theunitedstatesio
def import_export_transfer_theunitedstatesio_to_local_tables_view(request):
    """
    Take data from the local TheUnitedStatesIo database (TheUnitedStatesIoLegislatorCurrent)
    and transfer it to the We Vote data structures
    """
    # If person isn't signed in, we don't want to let them visit this page yet
    if not request.user.is_authenticated():
        return redirect('/admin')

    transfer_theunitedstatesio_cached_data_to_wevote_tables()

    template_values = {
        'politician_list': Politician.objects.order_by('last_name'),
    }
    return render(request, 'import_export/transfer_from_theunitedstatesio.html', template_values)
#
#
# def ValuesQuerySetToDict(data):
#     return [item for item in data]


def update_all_id_we_vote(request):
    """
    We just want to cycle through each of these data types and save so we populate the field id_we_vote
    :param request:
    :return:
    """
    candidate_campaign_list = CandidateCampaign.objects.all()
    for candidate_campaign in candidate_campaign_list:
        candidate_campaign.save()

    contest_measure_list = ContestMeasure.objects.all()
    for contest_measure in contest_measure_list:
        contest_measure.save()

    contest_office_list = ContestOffice.objects.all()
    for contest_office in contest_office_list:
        contest_office.save()

    measure_campaign_list = MeasureCampaign.objects.all()
    for measure_campaign in measure_campaign_list:
        measure_campaign.save()

    organization_list = Organization.objects.all()
    for organization in organization_list:
        organization.save()

    position_list = PositionEntered.objects.all()
    for position in position_list:
        position.save()


class ExportOrganizationDataToJson(APIView):
    def get(self, request, format=None):
        organization_list = Organization.objects.all()
        serializer = OrganizationSerializer(organization_list, many=True)
        return Response(serializer.data)


class ExportCandidateCampaignDataToJson(APIView):
    def get(self, request, format=None):
        candidate_campaign_list = CandidateCampaign.objects.all()
        serializer = CandidateCampaignSerializer(candidate_campaign_list, many=True)
        return Response(serializer.data)


class ExportPositionDataToJson(APIView):
    def get(self, request, format=None):
        position_list = PositionEntered.objects.all()
        # position_list = position_list.filter(organization_id0) # TODO DALE != ??? How do we do a not equal search
        serializer = PositionSerializer(position_list, many=True)
        return Response(serializer.data)


# TODO DALE This view is giving us this error:
# ValueError at /import_export/import_sample_positions/
# Not all temporary messages could be stored.
# Request Method:	GET
# Request URL:	http://localhost:8000/import_export/import_sample_positions/
def import_we_vote_sample_positions_data_from_json(request):
    """
    This gives us sample organizations, candidate campaigns, and positions for testing
    :return:
    """
    import_we_vote_organizations_from_json(request, False)

    # We are importing candidate_campaigns data (and not politician data) because all we are doing is making sure we
    #  sync to the same We Vote ID. This is critical so we can link Positions to Organization & Candidate Campaign.
    # At this point (June 2015) we assume the politicians have been imported from Google Civic. We aren't assigning
    # the politicians a We Vote id, but instead use their full name as the identifier
    import_we_vote_candidate_campaigns_from_json(request, False)

    import_we_vote_positions_from_json(request, False)

    messages.add_message(request, messages.INFO, 'Positions imported.')

    return HttpResponseRedirect(reverse('import_export:import_export_index', args=()))


def transfer_maplight_data_to_we_vote_tables(request):
    # TODO We need to perhaps set up a table for these mappings that volunteers can add to?
    #  We need a plan for how volunteers can help us add to these mappings
    # One possibility -- ask volunteers to update this Google Sheet, then write a csv importer:
    #  https://docs.google.com/spreadsheets/d/1havD7GCxmBhi-zLLMdOpSJlU_DtBjvb5IJNiXgno9Bk/edit#gid=0
    politician_name_mapping_list = []
    one_mapping = {
        "google_civic_name": "Betty T. Yee",
        "maplight_display_name": "Betty Yee",
        "maplight_original_name": "Betty T Yee",
    }
    politician_name_mapping_list.append(one_mapping)
    one_mapping = {
        "google_civic_name": "Edmund G. \"Jerry\" Brown",
        "maplight_display_name": "Jerry Brown",
        "maplight_original_name": "",
    }
    politician_name_mapping_list.append(one_mapping)

    candidate_campaign_manager = CandidateCampaignManager()

    maplight_candidates_current_query = MapLightCandidate.objects.all()

    for one_candidate_from_maplight_table in maplight_candidates_current_query:
        found_by_id = False
        # Try to find a matching candidate
        results = candidate_campaign_manager.retrieve_candidate_campaign_from_id_maplight(
            one_candidate_from_maplight_table.candidate_id)

        if not results['success']:
            logger.warn(u"Candidate NOT found by MapLight id: {name}".format(
                name=one_candidate_from_maplight_table.candidate_id
            ))
            results = candidate_campaign_manager.retrieve_candidate_campaign_from_candidate_name(
                one_candidate_from_maplight_table.display_name)

            if not results['success']:
                logger.warn(u"Candidate NOT found by display_name: {name}".format(
                    name=one_candidate_from_maplight_table.display_name
                ))
                results = candidate_campaign_manager.retrieve_candidate_campaign_from_candidate_name(
                    one_candidate_from_maplight_table.original_name)

                if not results['success']:
                    logger.warn(u"Candidate NOT found by original_name: {name}".format(
                        name=one_candidate_from_maplight_table.original_name
                    ))

                    one_mapping_google_civic_name = ''
                    for one_mapping_found in politician_name_mapping_list:
                        if value_exists(one_mapping_found['maplight_display_name']) \
                                and one_mapping_found['maplight_display_name'] == \
                                one_candidate_from_maplight_table.display_name:
                            one_mapping_google_civic_name = one_mapping_found['google_civic_name']
                            break
                    if value_exists(one_mapping_google_civic_name):
                        results = candidate_campaign_manager.retrieve_candidate_campaign_from_candidate_name(
                            one_mapping_google_civic_name)
                    if not results['success'] or not value_exists(one_mapping_google_civic_name):
                        logger.warn(u"Candidate NOT found by mapping to google_civic name: {name}".format(
                            name=one_mapping_google_civic_name
                        ))

                        continue  # Go to the next candidate

        candidate_campaign_on_stage = results['candidate_campaign']

        # Just in case the logic above let us through to here accidentally without a candidate_name value, don't proceed
        if not value_exists(candidate_campaign_on_stage.candidate_name):
            continue

        logger.debug(u"Candidate {name} found".format(
            name=candidate_campaign_on_stage.candidate_name
        ))

        try:
            # Tie the maplight id to our record
            if not found_by_id:
                candidate_campaign_on_stage.id_maplight = one_candidate_from_maplight_table.candidate_id

            # Bring over the photo
            candidate_campaign_on_stage.photo_url_from_maplight = one_candidate_from_maplight_table.photo

            # We can bring over other data as needed, like gender for example
            candidate_campaign_on_stage.save()
        except Exception as e:
            handle_record_not_saved_exception(e, logger=logger)

    messages.add_message(request, messages.INFO, 'MapLight data woven into We Vote tables.')

    return HttpResponseRedirect(reverse('import_export:import_export_index', args=()))
