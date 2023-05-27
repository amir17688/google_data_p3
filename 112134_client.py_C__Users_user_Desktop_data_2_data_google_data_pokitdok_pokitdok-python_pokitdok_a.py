# -*- coding: utf-8 -*-
#
# Copyright (C) 2014, All Rights Reserved, PokitDok, Inc.
# https://www.pokitdok.com
#
# Please see the License.txt file for more information.
# All other rights reserved.
#

from __future__ import absolute_import
import json
import os
import pokitdok
import requests
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient


class PokitDokClient(object):
    """
        PokitDok Platform API Client
        This class provides a wrapper around requests and requests-oauth
        to handle common API operations
    """
    def __init__(self, client_id, client_secret, base="https://platform.pokitdok.com", version="v4",
                 redirect_uri=None, scope=None, auto_refresh=False, token_refresh_callback=None, code=None):
        """
            Initialize a new PokitDok API Client

            :param client_id: The client id for your PokitDok Platform Application
            :param client_secret: The client secret for your PokitDok Platform Application
            :param base: The base URL to use for API requests.  Defaults to https://platform.pokitdok.com
            :param version: The API version that should be used for requests.  Defaults to the latest version.
            :param redirect_uri: The Redirect URI set for the PokitDok Platform Application.
                                 This value is managed at https://platform.pokitdok.com in the App Settings
            :param scope: a list of scope names that should be used when requesting authorization
            :param auto_refresh: Boolean to indicate whether or not access tokens should be automatically
                                 refreshed when they expire.
            :param token_refresh_callback: a function that should be called when token information is refreshed.
            :param code: code value received from an authorization code grant
        """
        self.base_headers = {
            'User-Agent': 'python-pokitdok/{0} {1}'.format(pokitdok.__version__, requests.utils.default_user_agent())
        }
        self.json_headers = {
            'Content-type': 'application/json',
        }
        self.json_headers.update(self.base_headers)
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.code = code
        self.auto_refresh = auto_refresh
        self.token_refresh_callback = token_refresh_callback
        self.token = {}
        self.url_base = "{0}/api/{1}".format(base, version)
        self.token_url = "{0}/oauth2/token".format(base)
        self.authorize_url = "{0}/oauth2/authorize".format(base)
        self.api_client = None
        self.fetch_access_token(code=self.code)

    def initialize_auth_api_client(self, refresh_url):
        self.api_client = OAuth2Session(self.client_id, redirect_uri=self.redirect_uri, scope=self.scope,
                                        auto_refresh_url=refresh_url, token_updater=self.token_refresh_callback,
                                        auto_refresh_kwargs={
                                            'client_id': self.client_id,
                                            'client_secret': self.client_secret})

    def authorization_url(self):
        """
            Construct OAuth2 Authorization Grant URL
            :return: (authorization url, state value) tuple
        """
        refresh_url = self.token_url if self.auto_refresh else None
        self.initialize_auth_api_client(refresh_url)
        return self.api_client.authorization_url(self.authorize_url)

    def fetch_access_token(self, code=None):
        """
            Retrieves an OAuth2 access token.  If `code` is not specified, the client_credentials
            grant type will be used based on the client_id and client_secret.  If `code` is not None,
            an authorization_code grant type will be used.
            :param code: optional code value obtained via an authorization grant
            :return: the client application's token information as a dictionary
        """
        refresh_url = self.token_url if self.auto_refresh else None
        if code is None:

            self.api_client = OAuth2Session(self.client_id, client=BackendApplicationClient(self.client_id),
                                            auto_refresh_url=refresh_url, token_updater=self.token_refresh_callback,
                                            auto_refresh_kwargs={
                                                'client_id': self.client_id,
                                                'client_secret': self.client_secret})
            self.token = self.api_client.fetch_token(self.token_url, client_id=self.client_id,
                                                     client_secret=self.client_secret)
        else:
            self.code = code
            self.initialize_auth_api_client(refresh_url)
            self.token = self.api_client.fetch_token(self.token_url, code=code, client_id=self.client_id,
                                                     client_secret=self.client_secret, scope=self.scope)
        return self.token

    def request(self, path, method='get', data=None, files=None, **kwargs):
        """
        General method for submitting an API request

        :param path: the API request path
        :param method: the http request method that should be used
        :param data: dictionary of request data that should be used for post/put requests
        :param files: dictionary of file information when the API accepts file uploads as input
        :param kwargs: optional keyword arguments to be relayed along as request parameters
        :return:
        """
        if data and not files:
            headers = self.json_headers
            request_data = json.dumps(data)
        else:
            headers = self.base_headers
            request_data = data

        request_url = "{0}{1}".format(self.url_base, path)
        request_method = getattr(self.api_client, method)
        return request_method(request_url, data=request_data, files=files, params=kwargs, headers=headers).json()

    def get(self, path, **kwargs):
        """
            Convenience method for submitting a GET API request via the `request` method
        """
        return self.request(path, method='get', **kwargs)

    def put(self, path, **kwargs):
        """
            Convenience method for submitting a PUT API request via the `request` method
        """
        return self.request(path, method='put', **kwargs)

    def post(self, path, **kwargs):
        """
            Convenience method for submitting a POST API request via the `request` method
        """
        return self.request(path, method='post', **kwargs)

    def delete(self, path, **kwargs):
        """
            Convenience method for submitting a DELETE API request via the `request` method
        """
        return self.request(path, method='delete', **kwargs)

    def activities(self, activity_id=None, **kwargs):
        """
            Fetch platform activity information

            :param activity_id: the id of a specific platform activity that should be retrieved.
                                If omitted, an index listing of activities is returned.  If included
                                other keyword arguments are ignored.

            Keyword arguments that may be used to refine an activity search:

            :param parent_id: The parent activity id of the activities.  This is used to track
                              child activities that are the result of a batch operation.

        """
        path = "/activities/{0}".format(activity_id if activity_id else '')
        return self.get(path, **kwargs)

    def cash_prices(self, **kwargs):
        """
            Fetch cash price information
        """
        return self.get('/prices/cash', **kwargs)

    def ccd(self, ccd_request):
        """
            Submit a continuity of care document (CCD) request

            :param ccd_request: dictionary representing a CCD request
        """
        return self.post('/ccd/', data=ccd_request)

    def claims(self, claims_request):
        """
            Submit a claims request

            :param claims_request: dictionary representing a claims request
        """
        return self.post('/claims/', data=claims_request)

    def claims_status(self, claims_status_request):
        """
            Submit a claims status request

            :param claims_status_request: dictionary representing a claims status request
        """
        return self.post('/claims/status', data=claims_status_request)

    def mpc(self, code=None, **kwargs):
        """
            Access clinical and consumer friendly information related to medical procedures

            :param code: A specific procedure code that should be used to retrieve information

            Keyword arguments that may be used to refine a medical procedure search:

            :param name: Search medical procedure information by consumer friendly name
            :param description: A partial or full description to be used to locate medical procedure information
        """
        mpc_path = "/mpc/{0}".format(code if code else '')
        return self.get(mpc_path, **kwargs)

    def icd_convert(self, code):
        """
            Locate the appropriate diagnosis mapping for the specified ICD-9 code

            :param code: A diagnosis code that should be used to retrieve information
        """
        return self.get("/icd/convert/{0}".format(code))

    def claims_convert(self, x12_claims_file):
        """
            Submit a raw X12 837 file to convert to a claims API request and map any ICD-9 codes to ICD-10

            :param x12_claims_file: the path to a X12 claims file to be submitted to the platform for processing
        """
        return self.post('/claims/convert', files={
            'file': (os.path.split(x12_claims_file)[-1], open(x12_claims_file, 'rb'), 'application/EDI-X12')
        })

    def eligibility(self, eligibility_request):
        """
            Submit an eligibility request

            :param eligibility_request: dictionary representing an eligibility request
        """
        return self.post('/eligibility/', data=eligibility_request)

    def enrollment(self, enrollment_request):
        """
            Submit a benefits enrollment/maintenance request

            :param enrollment_request: dictionary representing an enrollment request
        """
        return self.post('/enrollment/', data=enrollment_request)

    def enrollment_snapshot(self, trading_partner_id, x12_file):
        """
            Submit a X12 834 file to the platform to establish the enrollment information within it
            as the current membership enrollment snapshot for a trading partner

            :param trading_partner_id: the trading partner associated with the enrollment snapshot
            :param x12_file: the path to a X12 834 file that contains the current membership enrollment information
        """
        return self.post('/enrollment/snapshot', data={'trading_partner_id': trading_partner_id},
                         files={
                             'file': (os.path.split(x12_file)[-1], open(x12_file, 'rb'), 'application/EDI-X12')
                         })

    def enrollment_snapshots(self, snapshot_id=None, **kwargs):
        """
            List enrollment snapshots that are stored for the client application
        """
        path = "/enrollment/snapshot{0}".format('/{0}'.format(snapshot_id) if snapshot_id else '')
        return self.get(path, **kwargs)

    def enrollment_snapshot_data(self, snapshot_id, **kwargs):
        """
            List enrollment request objects that make up the specified enrollment snapshot

            :param snapshot_id: the enrollment snapshot id for the enrollment data
        """
        path = "/enrollment/snapshot/{0}/data".format(snapshot_id)
        return self.get(path, **kwargs)

    def files(self, trading_partner_id, x12_file):
        """
            Submit a raw X12 file to the platform for processing

            :param trading_partner_id: the trading partner that should receive the X12 file information
            :param x12_file: the path to a X12 file to be submitted to the platform for processing
        """
        return self.post('/files/', data={'trading_partner_id': trading_partner_id},
                         files={
                             'file': (os.path.split(x12_file)[-1], open(x12_file, 'rb'), 'application/EDI-X12')
                         })

    def insurance_prices(self, **kwargs):
        """
            Fetch insurance price information
        """
        return self.get('/prices/insurance', **kwargs)

    def payers(self, **kwargs):
        """
            Fetch payer information for supported trading partners

        """
        return self.get('/payers/',  **kwargs)

    def plans(self, **kwargs):
        """
            Fetch insurance plans information
        """
        return self.get('/plans/', **kwargs)

    def providers(self, npi=None, **kwargs):
        """
            Search health care providers in the PokitDok directory

            :param npi: The National Provider Identifier for an Individual Provider or Organization
                        When a NPI value is specified, no other parameters will be considered.

            Keyword arguments that may be used to refine a providers search:

            :param address_lines: Any or all of number, street name, apartment, suite number 
            :param zipcode: Zip code to search in
            :param city: City to search in
            :param state: State to search in
            :param radius: A value representing the search distance from a geographic center point
                           May be expressed in miles like: 10mi.  zipcode or city and state must
                           be provided to enable distance sorting with specified radius
            :param first_name: The first name of a provider to include in the search criteria
            :param last_name: The last name of a provider to include in the search criteria
            :param organization_name: The organization_name of a provider.  Do not pass first_name 
                                      or last_name with this argument
            :param limit: The number of provider results that should be included in search results
            :param sort: Accepted values include 'distance' (default) or 'rank'.  'distance' sort 
                         requires city & state or zipcode parameters otherwise sort will be 'rank'.

        """
        path = "/providers/{0}".format(npi if npi else '')
        return self.get(path, **kwargs)

    def trading_partners(self, trading_partner_id=None):
        """
            Search trading partners in the PokitDok Platform

            :param trading_partner_id: the ID used by PokitDok to uniquely identify a trading partner

            :returns a dictionary containing the specified trading partner or, if called with no arguments, a list of
                     available trading partners
        """
        path = "/tradingpartners/{0}".format(trading_partner_id if trading_partner_id else '')
        return self.get(path)

    def referrals(self, referral_request):
        """
            Submit a referral request
            :param referral_request: dictionary representing a referral request
        """
        return self.post('/referrals/', data=referral_request)

    def authorizations(self, authorizations_request):
        """
            Submit an authorization request
            :param authorizations_request: dictionary representing an authorization request
        """
        return self.post('/authorizations/', data=authorizations_request)

    def schedulers(self, scheduler_uuid=None):
        """
            Get information about supported scheduling systems or fetch data about a specific scheduling system
            :param scheduler_uuid: The uuid of a specific scheduling system.
        """
        path = "/schedule/schedulers/{0}".format(scheduler_uuid if scheduler_uuid else '')
        return self.get(path)

    def appointment_types(self, appointment_type_uuid=None):
        """
            Get information about appointment types or fetch data about a specific appointment type
            :param appointment_type_uuid: The uuid of a specific appointment type.
        """
        path = "/schedule/appointmenttypes/{0}".format(appointment_type_uuid if appointment_type_uuid else '')
        return self.get(path)

    def schedule_slots(self, slots_request):
        """
            Submit an open slot for a provider's schedule
            :param slots_request: dictionary representing a slots request
        """
        return self.post("/schedule/slots/", data=slots_request)

    def appointments(self, appointment_uuid=None, **kwargs):
        """
            Query for open appointment slots or retrieve information for a specific appointment
            :param appointment_uuid: The uuid of a specific appointment.
        """
        path = "/schedule/appointments/{0}".format(appointment_uuid if appointment_uuid else '')
        return self.get(path, **kwargs)

    def book_appointment(self, appointment_uuid, appointment_request):
        """
            Book an appointment
            :param appointment_uuid: The uuid of a specific appointment to be booked.
            :param appointment_request: the appointment request data
        """
        path = "/schedule/appointments/{0}".format(appointment_uuid)
        return self.put(path, data=appointment_request)

    update_appointment = book_appointment

    def cancel_appointment(self, appointment_uuid):
        """
            Cancel an appointment
            :param appointment_uuid: The uuid of a specific appointment.
        """
        path = "/schedule/appointments/{0}".format(appointment_uuid)
        return self.delete(path)

    def create_identity(self, identity_request):
        """
            Creates an identity resource.
            :param identity_request: The dictionary containing the identity request data.
            :returns: The new identity resource.
        """
        return self.post('/identity/', data=identity_request)

    def update_identity(self, identity_uuid, identity_request):
        """
           Updates an existing identity resource.
           :param identity_uuid: The identity resource's uuid.
           :param identity_request: The updated identity resource.
           :returns: The updated identity resource.
        """
        path = "/identity/{0}".format(identity_uuid)
        return self.put(path, data=identity_request)

    def identity(self, identity_uuid=None, **kwargs):
        """
            Queries for an existing identity resource by uuid or for multiple resources using parameters.
            :uuid: The identity resource uuid. Used to execute an exact match query by uuid.
            :kwargs: Additional query parameters using resource fields such as first_name, last_name, email, etc.
            :returns: list containing the search results. A search by uuid returns an empty list or a list containing
            a single identity record.
        """
        path = "/identity{0}".format('/{0}'.format(identity_uuid) if identity_uuid else '')
        return self.get(path, **kwargs)

    def identity_history(self, identity_uuid, historical_version=None):
        """
            Queries for an identity record's history.
            Returns a history summary including the insert date and version number or a specific record version, if
            the historical_version argument is provided.
            :param identity_uuid: The identity resource's uuid.
            :param historical_version: The historical version id. Used to return a historical identity record
            :return: history result (list)
        """
        identity_url = "{0}/identity/{1}/history".format(self.url_base, str(identity_uuid))

        if historical_version is not None:
            identity_url = "{0}/{1}".format(identity_url, historical_version)

        return self.api_client.get(identity_url, headers=self.base_headers).json()

    def pharmacy_plans(self, **kwargs):
        """
            Search drug plan information by trading partner and various plan identifiers

            :param kwargs: pharmacy plans API request parameters
            :return: drug plan information if a match is found
        """
        return self.get('/pharmacy/plans', **kwargs)

    def pharmacy_formulary(self, **kwargs):
        """
            Search drug plan formulary information to determine if a drug is covered by the specified
            drug plan.

            :param kwargs: pharmacy formulary API request parameters
            :return: formulary information if a match is found
        """
        return self.get('/pharmacy/formulary', **kwargs)

    def pharmacy_drug_cost(self, **kwargs):
        """
            Obtain drug cost estimates for a specific drug plan.

            :param kwargs: pharmacy drug cost API request parameters
            :return: cost estimates for all matching drugs
        """
        return self.get('/pharmacy/drug/cost', **kwargs)

    def pharmacy_network(self, npi=None, **kwargs):
        """
            Search for in-network pharmacies

            :param npi: The National Provider Identifier for a pharmacy
            :param kwargs: pharmacy network API request parameters
            :return: If an NPI is included in the request, details about the pharmacy are returned.
            Otherwise, a list of in-network pharmacies is returned.
        """
        path = "/pharmacy/network/{0}".format(npi) if npi else '/pharmacy/network'
        return self.get(path, **kwargs)
