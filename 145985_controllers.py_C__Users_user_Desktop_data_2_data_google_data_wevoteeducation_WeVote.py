# import_export/controllers.py
# Brought to you by We Vote. Be good.
# -*- coding: UTF-8 -*-


from election_office_measure.models import Election
from exception.models import handle_record_not_found_exception, \
    handle_record_not_saved_exception
from .models import transfer_theunitedstatesio_cached_data_to_wevote_tables, google_civic_save_election, \
    google_civic_get_or_create_candidate_campaign_basic, google_civic_get_or_create_politician, \
    google_civic_get_or_create_contest_office
from import_export_google_civic.models import GoogleCivicCandidateCampaign
from import_export_theunitedstatesio.controllers import import_legislators_current_csv
import wevote_functions.admin


logger = wevote_functions.admin.get_logger(__name__)


def import_politician_data_from_theunitedstatesio():
    """
    In this method, we import TheUnitedStates.io source data to a local table cache, and then take the cached
    data and move it/merge it with core We Vote data
    :return:
    """
    import_legislators_current_csv()
    transfer_theunitedstatesio_cached_data_to_wevote_tables()


def transfer_google_civic_voterinfo_cached_data_to_wevote_tables():
    """
    In this method, we take the cached google civic data and move it into the core We Vote data with some grooming
    :return:
    """
    logger.info("Running transfer_google_civic_voterinfo_cached_data_to_wevote_tables()")

    # Capture election information
    google_civic_save_election()

    # Politician linking
    google_civic_link_politician_to_campaign()

    # CandidateCampaign

    # ContestMeasure

    # MeasureCampaign

    # Populate BallotItem


def google_civic_link_politician_to_campaign():

    # Bring in the GoogleCivicCandidateCampaign and save the CandidateCampaign
    google_civic_candidate_campaign_query = GoogleCivicCandidateCampaign.objects.all()

    for google_civic_candidate_campaign_entry in google_civic_candidate_campaign_query:

        if not google_civic_candidate_campaign_entry.google_civic_election_id:
            logger.error(u"We cannot proceed with {name} -- there is no google_civic_election_id".format(
                name=google_civic_candidate_campaign_entry.name
            ))
            continue

        try:
            election_query = Election.objects.all()
            election_query = election_query.filter(
                google_civic_election_id=google_civic_candidate_campaign_entry.google_civic_election_id)

            if len(election_query) == 1:
                election_on_stage = election_query[0]
            else:
                logger.error(
                    "Break out of main loop without an election_on_stage -- single Election entry not found"
                )
                continue
        except Exception as e:
            handle_record_not_found_exception(e, logger=logger)
            continue

        ###########################################
        # Election
        # The election is linked below

        ###########################################
        # ContestOffice
        # We want to find or create a We Vote ContestOffice
        results = google_civic_get_or_create_contest_office(google_civic_candidate_campaign_entry, election_on_stage)
        try:
            contest_office_error = results['error_result']
            if contest_office_error:
                logger.error(
                    "Returned in google_civic_get_or_create_contest_office"\
                    "(skipping to next google_civic_candidate_campaign_entry)"
                )
                continue
            contest_office_on_stage = results['contest_office_on_stage']
            # contest_office_created = results['contest_office_created']

            # Link this ContestOffice to the Election that was created above
            contest_office_on_stage.election_id = election_on_stage.id
            contest_office_on_stage.save()  # We save here AND lower in case there are failures
        except Exception as e:
            handle_record_not_saved_exception(e, logger=logger)
            continue

        ###########################################
        # CandidateCampaign
        # We want to find or create a We Vote CandidateCampaign
        results = google_civic_get_or_create_candidate_campaign_basic(google_civic_candidate_campaign_entry)
        candidate_campaign_error = results['error_result']
        if candidate_campaign_error:
            logger.error(
                "Returned in google_civic_get_or_create_candidate_campaign_basic "\
                "(skipping to next google_civic_candidate_campaign_entry)"
            )
            continue
        # politician_link_needed = results['politician_link_needed']
        # candidate_campaign_created = results['candidate_campaign_created']
        candidate_campaign_on_stage = results['candidate_campaign_on_stage']

        try:
            # Add/update campaign information
            candidate_campaign_on_stage.candidate_name = google_civic_candidate_campaign_entry.name
            candidate_campaign_on_stage.party = google_civic_candidate_campaign_entry.party

            # Link this CandidateCampaign to the Election and ContestOffice that was created above
            candidate_campaign_on_stage.election_id = election_on_stage.id
            candidate_campaign_on_stage.google_civic_election_id = \
                google_civic_candidate_campaign_entry.google_civic_election_id
            candidate_campaign_on_stage.contest_office_id = contest_office_on_stage.id
            candidate_campaign_on_stage.save()

            # We want to save the local id back to the GoogleCivicCandidateCampaign table
            # so we can cross-check data-integrity
            # NOTE: We do not limit this linkage to when we first create these local entries
            google_civic_candidate_campaign_entry.we_vote_election_id = election_on_stage.id
            google_civic_candidate_campaign_entry.we_vote_contest_office_id = contest_office_on_stage.id
            google_civic_candidate_campaign_entry.we_vote_candidate_campaign_id = candidate_campaign_on_stage.id
            google_civic_candidate_campaign_entry.save()  # We save here AND lower in case there are failures
        except Exception as e:
            handle_record_not_saved_exception(e, logger=logger)
            continue

        ###########################################
        # Politician
        # We know that a politician is not currently linked to this campaign
        # if politician_link_needed:  # DALE 2015-05-03 I would like this to always refresh
        results = google_civic_get_or_create_politician(google_civic_candidate_campaign_entry)
        politician_error = results['error_result']
        if politician_error:
            logger.error(
                "Returned in google_civic_get_or_create_politician "\
                "(skipping to next google_civic_candidate_campaign_entry)"
            )
            continue
        politician_on_stage = results['politician_on_stage']

        try:
            candidate_campaign_on_stage.politician_id = politician_on_stage.id
            candidate_campaign_on_stage.save()

            google_civic_candidate_campaign_entry.we_vote_politician_id = politician_on_stage.id
            google_civic_candidate_campaign_entry.save()
        except Exception as e:
            handle_record_not_saved_exception(e, logger=logger)
            continue
    # END OF google_civic_link_politician_to_campaign
