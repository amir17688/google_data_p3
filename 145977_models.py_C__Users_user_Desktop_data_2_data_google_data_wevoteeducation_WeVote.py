# election_office_measure/models.py
# Brought to you by We Vote. Be good.
# -*- coding: UTF-8 -*-

from django.db import models
from exception.models import handle_record_found_more_than_one_exception
from wevote_settings.models import fetch_next_id_we_vote_last_candidate_campaign_integer, \
    fetch_next_id_we_vote_last_contest_measure_integer, fetch_next_id_we_vote_last_contest_office_integer, \
    fetch_next_id_we_vote_last_measure_campaign_integer, fetch_site_unique_id_prefix
import wevote_functions.admin


logger = wevote_functions.admin.get_logger(__name__)


class Election(models.Model):
    # The unique ID of this election. (Provided by Google Civic)
    google_civic_election_id = models.CharField(verbose_name="google civic election id",
                                                max_length=20, null=True, unique=True)
    # A displayable name for the election.
    name = models.CharField(verbose_name="election name", max_length=254, null=False, blank=False)
    # Day of the election in YYYY-MM-DD format.
    election_date_text = models.CharField(verbose_name="election day", max_length=254, null=False, blank=False)


class ContestOffice(models.Model):
    # The id_we_vote identifier is unique across all We Vote sites, and allows us to share our data with other
    # organizations
    # It starts with "wv" then we add on a database specific identifier like "3v" (WeVoteSetting.site_unique_id_prefix)
    # then the string "off", and then a sequential integer like "123".
    # We keep the last value in WeVoteSetting.id_we_vote_last_contest_office_integer
    id_we_vote = models.CharField(
        verbose_name="we vote permanent id", max_length=255, default=None, null=True, blank=True, unique=True)
    # The name of the office for this contest.
    office_name = models.CharField(verbose_name="google civic office", max_length=254, null=False, blank=False)
    # The We Vote unique id for the election
    election_id = models.CharField(verbose_name="we vote election id", max_length=254, null=False, blank=False)
    # The unique ID of the election containing this contest. (Provided by Google Civic)
    google_civic_election_id = models.CharField(verbose_name="google civic election id",
                                                max_length=254, null=False, blank=False)
    id_cicero = models.CharField(
        verbose_name="azavea cicero unique identifier", max_length=254, null=True, blank=True, unique=True)
    id_maplight = models.CharField(
        verbose_name="maplight unique identifier", max_length=254, null=True, blank=True, unique=True)
    id_ballotpedia = models.CharField(
        verbose_name="ballotpedia unique identifier", max_length=254, null=True, blank=True)
    id_wikipedia = models.CharField(verbose_name="wikipedia unique identifier", max_length=254, null=True, blank=True)
    # vote_type (ranked choice, majority)

    # ballot_placement: NOTE - even though GoogleCivicContestOffice has this field, we store this value
    #  in the BallotItem table instead because it is different for each voter

    # The number of candidates that a voter may vote for in this contest.
    number_voting_for = models.CharField(verbose_name="number of candidates to vote for",
                                         max_length=254, null=True, blank=True)
    # The number of candidates that will be elected to office in this contest.
    number_elected = models.CharField(verbose_name="number of candidates who will be elected",
                                      max_length=254, null=True, blank=True)
    # If this is a partisan election, the name of the party it is for.
    primary_party = models.CharField(verbose_name="primary party", max_length=254, null=True, blank=True)
    # The name of the district.
    district_name = models.CharField(verbose_name="district name", max_length=254, null=False, blank=False)
    # The geographic scope of this district. If unspecified the district's geography is not known.
    # One of: national, statewide, congressional, stateUpper, stateLower, countywide, judicial, schoolBoard,
    # cityWide, township, countyCouncil, cityCouncil, ward, special
    district_scope = models.CharField(verbose_name="district scope", max_length=254, null=False, blank=False)
    # An identifier for this district, relative to its scope. For example, the 34th State Senate district
    # would have id "34" and a scope of stateUpper.
    district_ocd_id = models.CharField(verbose_name="open civic data id", max_length=254, null=False, blank=False)

    # We override the save function so we can auto-generate id_we_vote
    def save(self, *args, **kwargs):
        # Even if this data came from another source we still need a unique id_we_vote
        if self.id_we_vote:
            self.id_we_vote = self.id_we_vote.strip()
        if self.id_we_vote == "" or self.id_we_vote is None:  # If there isn't a value...
            # ...generate a new id
            site_unique_id_prefix = fetch_site_unique_id_prefix()
            next_local_integer = fetch_next_id_we_vote_last_contest_office_integer()
            # "wv" = We Vote
            # site_unique_id_prefix = a generated (or assigned) unique id for one server running We Vote
            # "off" = tells us this is a unique id for a ContestOffice
            # next_integer = a unique, sequential integer for this server - not necessarily tied to database id
            self.id_we_vote = "wv{site_unique_id_prefix}off{next_integer}".format(
                site_unique_id_prefix=site_unique_id_prefix,
                next_integer=next_local_integer,
            )
        super(ContestOffice, self).save(*args, **kwargs)


class ContestOfficeManager(models.Model):

    def __unicode__(self):
        return "ContestOfficeManager"

    def retrieve_contest_office_from_id(self, contest_office_id):
        contest_office_manager = ContestOfficeManager()
        return contest_office_manager.retrieve_contest_office(contest_office_id)

    def retrieve_contest_office_from_id_maplight(self, id_maplight):
        contest_office_id = 0
        contest_office_manager = ContestOfficeManager()
        return contest_office_manager.retrieve_contest_office(contest_office_id, id_maplight)

    def fetch_contest_office_id_from_id_maplight(self, id_maplight):
        contest_office_id = 0
        contest_office_manager = ContestOfficeManager()
        results = contest_office_manager.retrieve_contest_office(contest_office_id, id_maplight)
        if results['success']:
            return results['contest_office_id']
        return 0

    # NOTE: searching by all other variables seems to return a list of objects
    def retrieve_contest_office(self, contest_office_id, id_maplight=None):
        error_result = False
        exception_does_not_exist = False
        exception_multiple_object_returned = False
        contest_office_on_stage = ContestOffice()

        try:
            if contest_office_id > 0:
                contest_office_on_stage = ContestOffice.objects.get(id=contest_office_id)
                contest_office_id = contest_office_on_stage.id
            elif len(id_maplight) > 0:
                contest_office_on_stage = ContestOffice.objects.get(id_maplight=id_maplight)
                contest_office_id = contest_office_on_stage.id
        except ContestOffice.MultipleObjectsReturned as e:
            handle_record_found_more_than_one_exception(e, logger=logger)
            exception_multiple_object_returned = True
        except ContestOffice.DoesNotExist as e:
            exception_does_not_exist = True

        results = {
            'success':                  True if contest_office_id > 0 else False,
            'error_result':             error_result,
            'DoesNotExist':             exception_does_not_exist,
            'MultipleObjectsReturned':  exception_multiple_object_returned,
            'contest_office_found':     True if contest_office_id > 0 else False,
            'contest_office_id':        contest_office_id,
            'contest_office':           contest_office_on_stage,
        }
        return results


class CandidateCampaignList(models.Model):
    """
    This is a class to make it easy to retrieve lists of Candidates
    """

    def retrieve_candidate_campaigns_for_this_election_list(self):
        candidates_list_temp = CandidateCampaign.objects.all()
        # Order by candidate_name.
        # To order by last name we will need to make some guesses in some case about what the last name is.
        candidates_list_temp = candidates_list_temp.order_by('candidate_name')
        candidates_list_temp = candidates_list_temp.filter(election_id=1)  # TODO Temp election_id
        return candidates_list_temp


class CandidateCampaign(models.Model):
    # The id_we_vote identifier is unique across all We Vote sites, and allows us to share our data with other
    # organizations
    # It starts with "wv" then we add on a database specific identifier like "3v" (WeVoteSetting.site_unique_id_prefix)
    # then the string "cand", and then a sequential integer like "123".
    # We keep the last value in WeVoteSetting.id_we_vote_last_candidate_campaign_integer
    id_we_vote = models.CharField(
        verbose_name="we vote permanent id", max_length=255, default=None, null=True, blank=True, unique=True)
    id_maplight = models.CharField(
        verbose_name="maplight candidate id", max_length=255, default=None, null=True, blank=True, unique=True)
    # election link to local We Vote Election entry. During setup we need to allow this to be null.
    election_id = models.IntegerField(verbose_name="election unique identifier", null=True, blank=True)
    # The internal We Vote id for the ContestOffice that this candidate is competing for.
    # During setup we need to allow this to be null.
    contest_office_id = models.CharField(
        verbose_name="contest_office_id id", max_length=254, null=True, blank=True)
    # politician link to local We Vote Politician entry. During setup we need to allow this to be null.
    politician_id = models.IntegerField(verbose_name="politician unique identifier", null=True, blank=True)
    # The candidate's name.
    candidate_name = models.CharField(verbose_name="candidate name", max_length=254, null=False, blank=False)
    # The full name of the party the candidate is a member of.
    party = models.CharField(verbose_name="party", max_length=254, null=True, blank=True)
    # A URL for a photo of the candidate.
    photo_url = models.CharField(verbose_name="photoUrl", max_length=254, null=True, blank=True)
    photo_url_from_maplight = models.URLField(verbose_name='candidate portrait url of candidate', blank=True, null=True)
    # The order the candidate appears on the ballot for this contest.
    order_on_ballot = models.CharField(verbose_name="order on ballot", max_length=254, null=True, blank=True)
    # The unique ID of the election containing this contest. (Provided by Google Civic)
    google_civic_election_id = models.CharField(
        verbose_name="google civic election id", max_length=254, null=True, blank=True)
    # The URL for the candidate's campaign web site.
    candidate_url = models.URLField(verbose_name='website url of candidate campaign', blank=True, null=True)
    facebook_url = models.URLField(verbose_name='facebook url of candidate campaign', blank=True, null=True)
    twitter_url = models.URLField(verbose_name='twitter url of candidate campaign', blank=True, null=True)
    google_plus_url = models.URLField(verbose_name='google plus url of candidate campaign', blank=True, null=True)
    youtube_url = models.URLField(verbose_name='youtube url of candidate campaign', blank=True, null=True)
    # The email address for the candidate's campaign.
    email = models.CharField(verbose_name="candidate campaign email", max_length=254, null=True, blank=True)
    # The voice phone number for the candidate's campaign office.
    phone = models.CharField(verbose_name="candidate campaign email", max_length=254, null=True, blank=True)

    def fetch_photo_url(self):
        if self.photo_url_from_maplight:
            return self.photo_url_from_maplight
        elif self.photo_url:
            return self.photo_url
        else:
            return ""
            # "http://votersedge.org/sites/all/modules/map/modules/map_proposition/images/politicians/2662.jpg"
        # else:
        #     politician_manager = PoliticianManager()
        #     return politician_manager.fetch_photo_url(self.politician_id)

    # We override the save function so we can auto-generate id_we_vote
    def save(self, *args, **kwargs):
        # Even if this data came from another source we still need a unique id_we_vote
        if self.id_we_vote:
            self.id_we_vote = self.id_we_vote.strip()
        if self.id_we_vote == "" or self.id_we_vote is None:  # If there isn't a value...
            # ...generate a new id
            site_unique_id_prefix = fetch_site_unique_id_prefix()
            next_local_integer = fetch_next_id_we_vote_last_candidate_campaign_integer()
            # "wv" = We Vote
            # site_unique_id_prefix = a generated (or assigned) unique id for one server running We Vote
            # "cand" = tells us this is a unique id for a CandidateCampaign
            # next_integer = a unique, sequential integer for this server - not necessarily tied to database id
            self.id_we_vote = "wv{site_unique_id_prefix}cand{next_integer}".format(
                site_unique_id_prefix=site_unique_id_prefix,
                next_integer=next_local_integer,
            )
        if self.id_maplight == "":  # We want this to be unique IF there is a value, and otherwise "None"
            self.id_maplight = None
        super(CandidateCampaign, self).save(*args, **kwargs)


#
def mimic_google_civic_initials(name):
    modified_name = name.replace(' A ', ' A. ')
    modified_name = modified_name.replace(' B ', ' B. ')
    modified_name = modified_name.replace(' C ', ' C. ')
    modified_name = modified_name.replace(' D ', ' D. ')
    modified_name = modified_name.replace(' E ', ' E. ')
    modified_name = modified_name.replace(' F ', ' F. ')
    modified_name = modified_name.replace(' G ', ' G. ')
    modified_name = modified_name.replace(' H ', ' H. ')
    modified_name = modified_name.replace(' I ', ' I. ')
    modified_name = modified_name.replace(' J ', ' J. ')
    modified_name = modified_name.replace(' K ', ' K. ')
    modified_name = modified_name.replace(' L ', ' L. ')
    modified_name = modified_name.replace(' M ', ' M. ')
    modified_name = modified_name.replace(' N ', ' N. ')
    modified_name = modified_name.replace(' O ', ' O. ')
    modified_name = modified_name.replace(' P ', ' P. ')
    modified_name = modified_name.replace(' Q ', ' Q. ')
    modified_name = modified_name.replace(' R ', ' R. ')
    modified_name = modified_name.replace(' S ', ' S. ')
    modified_name = modified_name.replace(' T ', ' T. ')
    modified_name = modified_name.replace(' U ', ' U. ')
    modified_name = modified_name.replace(' V ', ' V. ')
    modified_name = modified_name.replace(' W ', ' W. ')
    modified_name = modified_name.replace(' X ', ' X. ')
    modified_name = modified_name.replace(' Y ', ' Y. ')
    modified_name = modified_name.replace(' Z ', ' Z. ')
    return modified_name


class CandidateCampaignManager(models.Model):

    def __unicode__(self):
        return "CandidateCampaignManager"

    def retrieve_candidate_campaign_from_id(self, candidate_campaign_id):
        candidate_campaign_manager = CandidateCampaignManager()
        return candidate_campaign_manager.retrieve_candidate_campaign(candidate_campaign_id)

    def retrieve_candidate_campaign_from_id_we_vote(self, id_we_vote):
        candidate_campaign_id = 0
        candidate_campaign_manager = CandidateCampaignManager()
        return candidate_campaign_manager.retrieve_candidate_campaign(candidate_campaign_id, id_we_vote)

    def fetch_candidate_campaign_id_from_id_we_vote(self, id_we_vote):
        candidate_campaign_id = 0
        candidate_campaign_manager = CandidateCampaignManager()
        results = candidate_campaign_manager.retrieve_candidate_campaign(candidate_campaign_id, id_we_vote)
        if results['success']:
            return results['candidate_campaign_id']
        return 0

    def retrieve_candidate_campaign_from_id_maplight(self, candidate_id_maplight):
        candidate_campaign_id = 0
        id_we_vote = ''
        candidate_campaign_manager = CandidateCampaignManager()
        return candidate_campaign_manager.retrieve_candidate_campaign(
            candidate_campaign_id, id_we_vote, candidate_id_maplight)

    def retrieve_candidate_campaign_from_candidate_name(self, candidate_name):
        candidate_campaign_id = 0
        id_we_vote = ''
        candidate_id_maplight = ''
        candidate_campaign_manager = CandidateCampaignManager()

        results = candidate_campaign_manager.retrieve_candidate_campaign(
            candidate_campaign_id, id_we_vote, candidate_id_maplight, candidate_name)
        if results['success']:
            return results

        # Try to modify the candidate name, and search again
        # MapLight for example will pass in "Ronald  Gold" for example
        candidate_name_try2 = candidate_name.replace('  ', ' ')
        results = candidate_campaign_manager.retrieve_candidate_campaign(
            candidate_campaign_id, id_we_vote, candidate_id_maplight, candidate_name_try2)
        if results['success']:
            return results

        # MapLight also passes in "Kamela D Harris" for example, and Google Civic uses "Kamela D. Harris"
        candidate_name_try3 = mimic_google_civic_initials(candidate_name)
        if candidate_name_try3 != candidate_name:
            results = candidate_campaign_manager.retrieve_candidate_campaign(
                candidate_campaign_id, id_we_vote, candidate_id_maplight, candidate_name_try3)
            if results['success']:
                return results

        # Otherwise return failed results
        return results

    # NOTE: searching by all other variables seems to return a list of objects
    def retrieve_candidate_campaign(
            self, candidate_campaign_id, id_we_vote=None, candidate_id_maplight=None, candidate_name=None):
        error_result = False
        exception_does_not_exist = False
        exception_multiple_object_returned = False
        candidate_campaign_on_stage = CandidateCampaign()

        try:
            if candidate_campaign_id > 0:
                candidate_campaign_on_stage = CandidateCampaign.objects.get(id=candidate_campaign_id)
                candidate_campaign_id = candidate_campaign_on_stage.id
            elif len(id_we_vote) > 0:
                candidate_campaign_on_stage = CandidateCampaign.objects.get(id_we_vote=id_we_vote)
                candidate_campaign_id = candidate_campaign_on_stage.id
            elif candidate_id_maplight > 0 and candidate_id_maplight != "":
                candidate_campaign_on_stage = CandidateCampaign.objects.get(id_maplight=candidate_id_maplight)
                candidate_campaign_id = candidate_campaign_on_stage.id
            elif len(candidate_name) > 0:
                candidate_campaign_on_stage = CandidateCampaign.objects.get(candidate_name=candidate_name)
                candidate_campaign_id = candidate_campaign_on_stage.id
        except CandidateCampaign.MultipleObjectsReturned as e:
            handle_record_found_more_than_one_exception(e, logger=logger)
            exception_multiple_object_returned = True
        except CandidateCampaign.DoesNotExist as e:
            exception_does_not_exist = True

        results = {
            'success':                  True if candidate_campaign_id > 0 else False,
            'error_result':             error_result,
            'DoesNotExist':             exception_does_not_exist,
            'MultipleObjectsReturned':  exception_multiple_object_returned,
            'candidate_campaign_found': True if candidate_campaign_id > 0 else False,
            'candidate_campaign_id':    candidate_campaign_id,
            'candidate_campaign':       candidate_campaign_on_stage,
        }
        return results


class ContestMeasure(models.Model):
    # The id_we_vote identifier is unique across all We Vote sites, and allows us to share our data with other
    # organizations
    # It starts with "wv" then we add on a database specific identifier like "3v" (WeVoteSetting.site_unique_id_prefix)
    # then the string "meas", and then a sequential integer like "123".
    # We keep the last value in WeVoteSetting.id_we_vote_last_contest_measure_integer
    id_we_vote = models.CharField(
        verbose_name="we vote permanent id", max_length=255, default=None, null=True, blank=True, unique=True)
    id_maplight = models.CharField(verbose_name="maplight unique identifier",
                                   max_length=254, null=True, blank=True, unique=True)
    # The title of the measure (e.g. 'Proposition 42').
    measure_title = models.CharField(verbose_name="measure title", max_length=254, null=False, blank=False)
    # A brief description of the referendum. This field is only populated for contests of type 'Referendum'.
    measure_subtitle = models.CharField(verbose_name="google civic referendum subtitle",
                                        max_length=254, null=False, blank=False)
    # A link to the referendum. This field is only populated for contests of type 'Referendum'.
    measure_url = models.CharField(verbose_name="measure details url", max_length=254, null=True, blank=False)
    # The We Vote unique id for the election
    election_id = models.CharField(verbose_name="we vote election id", max_length=254, null=False, blank=False)
    # The unique ID of the election containing this contest. (Provided by Google Civic)
    google_civic_election_id = models.CharField(verbose_name="election id", max_length=254, null=False, blank=False)
    # ballot_placement: NOTE - even though GoogleCivicContestOffice has this field, we store this value
    #  in the BallotItem table instead because it is different for each voter
    # If this is a partisan election, the name of the party it is for.
    primary_party = models.CharField(verbose_name="primary party", max_length=254, null=True, blank=True)
    # The name of the district.
    district_name = models.CharField(verbose_name="district name", max_length=254, null=False, blank=False)
    # The geographic scope of this district. If unspecified the district's geography is not known.
    # One of: national, statewide, congressional, stateUpper, stateLower, countywide, judicial, schoolBoard,
    # cityWide, township, countyCouncil, cityCouncil, ward, special
    district_scope = models.CharField(verbose_name="district scope", max_length=254, null=False, blank=False)
    # An identifier for this district, relative to its scope. For example, the 34th State Senate district
    # would have id "34" and a scope of stateUpper.
    district_ocd_id = models.CharField(verbose_name="open civic data id", max_length=254, null=False, blank=False)

    # We override the save function so we can auto-generate id_we_vote
    def save(self, *args, **kwargs):
        # Even if this data came from another source we still need a unique id_we_vote
        if self.id_we_vote:
            self.id_we_vote = self.id_we_vote.strip()
        if self.id_we_vote == "" or self.id_we_vote is None:  # If there isn't a value...
            # ...generate a new id
            site_unique_id_prefix = fetch_site_unique_id_prefix()
            next_local_integer = fetch_next_id_we_vote_last_contest_measure_integer()
            # "wv" = We Vote
            # site_unique_id_prefix = a generated (or assigned) unique id for one server running We Vote
            # "meas" = tells us this is a unique id for a ContestMeasure
            # next_integer = a unique, sequential integer for this server - not necessarily tied to database id
            self.id_we_vote = "wv{site_unique_id_prefix}meas{next_integer}".format(
                site_unique_id_prefix=site_unique_id_prefix,
                next_integer=next_local_integer,
            )
        super(ContestMeasure, self).save(*args, **kwargs)


class MeasureCampaign(models.Model):
    # The id_we_vote identifier is unique across all We Vote sites, and allows us to share our data with other
    # organizations
    # It starts with "wv" then we add on a database specific identifier like "3v" (WeVoteSetting.site_unique_id_prefix)
    # then the string "meascam", and then a sequential integer like "123".
    # We keep the last value in WeVoteSetting.id_we_vote_last_measure_campaign_integer
    id_we_vote = models.CharField(
        verbose_name="we vote permanent id", max_length=255, default=None, null=True, blank=True, unique=True)
    # contest_measure link
    # The internal We Vote id for the ContestMeasure that this campaign taking a stance on
    contest_measure_id = models.CharField(verbose_name="contest_measure unique id",
                                          max_length=254, null=False, blank=False)
    # Is the campaign attempting to pass the measure, or stop it from passing?
    SUPPORT = 'S'
    NEUTRAL = 'N'
    OPPOSE = 'O'
    STANCE_CHOICES = (
        (SUPPORT, 'Support'),
        (NEUTRAL, 'Neutral'),
        (OPPOSE, 'Oppose'),
    )
    stance = models.CharField("stance", max_length=1, choices=STANCE_CHOICES, default=NEUTRAL)

    # The candidate's name.
    candidate_name = models.CharField(verbose_name="candidate name", max_length=254, null=False, blank=False)
    # The full name of the party the candidate is a member of.
    party = models.CharField(verbose_name="party", max_length=254, null=True, blank=True)
    # A URL for a photo of the candidate.
    photo_url = models.CharField(verbose_name="photoUrl", max_length=254, null=True, blank=True)
    # The unique ID of the election containing this contest. (Provided by Google Civic)
    google_civic_election_id = models.CharField(verbose_name="google election id",
                                                max_length=254, null=False, blank=False)
    # The URL for the candidate's campaign web site.
    url = models.URLField(verbose_name='website url of campaign', blank=True, null=True)
    facebook_url = models.URLField(verbose_name='facebook url of campaign', blank=True, null=True)
    twitter_url = models.URLField(verbose_name='twitter url of campaign', blank=True, null=True)
    google_plus_url = models.URLField(verbose_name='google plus url of campaign', blank=True, null=True)
    youtube_url = models.URLField(verbose_name='youtube url of campaign', blank=True, null=True)
    # The email address for the candidate's campaign.
    email = models.CharField(verbose_name="campaign email", max_length=254, null=True, blank=True)
    # The voice phone number for the campaign office.
    phone = models.CharField(verbose_name="campaign email", max_length=254, null=True, blank=True)

    # We override the save function so we can auto-generate id_we_vote
    def save(self, *args, **kwargs):
        # Even if this data came from another source we still need a unique id_we_vote
        if self.id_we_vote:
            self.id_we_vote = self.id_we_vote.strip()
        if self.id_we_vote == "" or self.id_we_vote is None:  # If there isn't a value...
            # ...generate a new id
            site_unique_id_prefix = fetch_site_unique_id_prefix()
            next_local_integer = fetch_next_id_we_vote_last_measure_campaign_integer()
            # "wv" = We Vote
            # site_unique_id_prefix = a generated (or assigned) unique id for one server running We Vote
            # "meascam" = tells us this is a unique id for a MeasureCampaign
            # next_integer = a unique, sequential integer for this server - not necessarily tied to database id
            self.id_we_vote = "wv{site_unique_id_prefix}meascam{next_integer}".format(
                site_unique_id_prefix=site_unique_id_prefix,
                next_integer=next_local_integer,
            )
        super(MeasureCampaign, self).save(*args, **kwargs)


class BallotItem(models.Model):
    """
    This is a generated table with ballot item data from a variety of sources, including Google Civic
    (and MapLight, Ballot API Code for America project, and Azavea Cicero in the future)
    """
    # The unique id of the voter
    voter_id = models.IntegerField(verbose_name="the voter unique id", default=0, null=False, blank=False)
    # The We Vote unique ID of this election
    election_id = models.CharField(verbose_name="election id", max_length=20, null=True)
    # The unique ID of this election. (Provided by Google Civic)
    google_civic_election_id = models.CharField(verbose_name="google civic election id", max_length=20, null=True)
    # The internal We Vote id for the ContestOffice that this candidate is competing for
    contest_office_id = models.CharField(verbose_name="contest_office_id id", max_length=254, null=True, blank=True)
    # The internal We Vote id for the ContestMeasure that this campaign taking a stance on
    contest_measure_id = models.CharField(
        verbose_name="contest_measure unique id", max_length=254, null=True, blank=True)
    ballot_order = models.SmallIntegerField(
        verbose_name="the order this item should appear on the ballot", null=True, blank=True)
    # This is a sortable name
    ballot_item_label = models.CharField(verbose_name="a label we can sort by", max_length=254, null=True, blank=True)

    def is_contest_office(self):
        if self.contest_office_id:
            return True
        return False

    def is_contest_measure(self):
        if self.contest_measure_id:
            return True
        return False

    def display_ballot_item(self):
        return self.ballot_item_label

    def candidates_list(self):
        candidates_list_temp = CandidateCampaign.objects.all()
        candidates_list_temp = candidates_list_temp.filter(election_id=self.election_id)
        candidates_list_temp = candidates_list_temp.filter(contest_office_id=self.contest_office_id)
        return candidates_list_temp


class BallotItemManager(models.Model):

    def retrieve_all_ballot_items_for_voter(self, voter_id, election_id=0):
        ballot_item_list = BallotItem.objects.order_by('ballot_order')

        results = {
            'election_id':      election_id,
            'voter_id':         voter_id,
            'ballot_item_list': ballot_item_list,
        }
        return results

    # NOTE: This method only needs to hit the database at most once per day.
    # We should cache the results in a JSON file that gets cached on the server and locally in the
    # voter's browser for speed.
    def retrieve_my_ballot(voter_on_stage, election_on_stage):
        # Retrieve all of the jurisdictions the voter is in

        # Retrieve all of the office_contests in each of those jurisdictions

        # Retrieve all of the measure_contests in each of those jurisdictions
        return True
