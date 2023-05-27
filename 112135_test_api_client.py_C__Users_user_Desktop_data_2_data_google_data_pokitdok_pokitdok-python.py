from __future__ import absolute_import

import pokitdok
from httmock import urlmatch, HTTMock, response
import datetime
import json
import tests
import copy
from unittest import TestCase
import requests


class TestAPIClient(object):
    """
    Validates that PokitDok API client requests are well formed.
    Httmock (https://pypi.python.org/pypi/httmock/) is used to provide mock HTTP responses.
    """
    ASSERTION_EQ_MSG = 'Expected {} != Actual {}'
    BASE_HEADERS = {
        'User-Agent': 'python-pokitdok/{0} {1}'.format(pokitdok.__version__, requests.utils.default_user_agent())
    }
    BASE_URL = 'https://platform.pokitdok.com/v4/api'
    CLIENT_ID = 'F7q38MzlwOxUwTHb7jvk'
    CLIENT_SECRET = 'O8DRamKmKMLtSTPjK99eUlbfOQEc44VVmp8ARmcY'
    JSON_HEADERS = {
        'User-Agent': 'python-pokitdok/{0} {1}'.format(pokitdok.__version__, requests.utils.default_user_agent()),
        'Content-type': 'application/json',
    }
    MATCH_NETWORK_LOCATION = r'(.*\.)?pokitdok\.com'
    MATCH_OAUTH2_PATH = r'[/]oauth2[/]token'
    TEST_REQUEST_PATH = '/endpoint'

    def __init__(self):
        """
            Defines instance attributes used in test cases
            - pd_client = PokitDok API client instance
            - current_request = The requests request object for the current test case request
        """
        self.pd_client = None
        self.current_request = None

    @urlmatch(netloc=MATCH_NETWORK_LOCATION, path=MATCH_OAUTH2_PATH, method='POST')
    def mock_oauth2_token(self, url, request):
        """
            Returns a mocked OAuth2 token response
            :param url: The request url
            :param request: The requests request object
            :return: mocked OAuth2 token response
        """
        headers = {
            'Server': 'nginx',
            'Date': datetime.datetime.utcnow(),
            'Content-type': 'application/json;charset=UTF-8',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-store'
        }

        content = {
            'access_token': 's8KYRJGTO0rWMy0zz1CCSCwsSesDyDlbNdZoRqVR',
            'token_type': 'bearer',
            'expires': 1393350569,
            'expires_in': 3600
        }

        headers['Content-Length'] = len(json.dumps(content))

        return response(status_code=200, content=content, headers=headers, request=request)

    @urlmatch(netloc=MATCH_NETWORK_LOCATION)
    def mock_api_response(self, url, request):
        """
            Processes an incoming API request and returns a mocked response.
            The incoming API request is cached and made available to tests.
            :param url: The request url
            :param request: The requests request object
            :return: 200 status code response with an empty content body {}
        """
        self.current_request = request
        return response(status_code=200, content={}, request=request)

    def setUp(self):
        """
            Creates a new PokitDok client instance
        """
        with HTTMock(self.mock_oauth2_token):
            self.pd_client = pokitdok.api.connect(self.CLIENT_ID, self.CLIENT_SECRET)

    def test_connect(self):
        """
            Tests pokitdok.api.connect (PokitDok.__init__())
            Validates that the API client is instantiated and has an access token.
        """
        with HTTMock(self.mock_oauth2_token):
            self.pd_client = pokitdok.api.connect(self.CLIENT_ID, self.CLIENT_SECRET)

        assert self.pd_client.api_client is not None
        assert self.pd_client.api_client.token is not None

    def test_request_post(self):
        """
            Tests the PokitDok.request convenience method with a POST request.
            Validates that the requests request is configured correctly and has the appropriate headers.
        """
        with HTTMock(self.mock_api_response):
            self.pd_client.request(self.TEST_REQUEST_PATH, method='post', data={'param': 'value'})

        for k, v in self.JSON_HEADERS.items():
            assert k in self.current_request.headers

            actual_value = self.current_request.headers[k]
            assert v == self.current_request.headers[k], self.ASSERTION_EQ_MSG.format(v, actual_value)

        assert 'POST' == self.current_request.method

    def test_request_get(self):
        """
            Tests the PokitDok.request convenience method with a GET request.
            Validates that the requests request is configured correctly and has the appropriate headers.
        """
        with HTTMock(self.mock_api_response):
            self.pd_client.request(self.TEST_REQUEST_PATH, method='get')

        for k, v in self.BASE_HEADERS.items():
            assert k in self.current_request.headers

            actual_value = self.current_request.headers[k]
            assert v == self.current_request.headers[k], self.ASSERTION_EQ_MSG.format(v, actual_value)

        assert 'GET' == self.current_request.method

    def test_get(self):
        """
            Tests the PokitDok.get convenience method.
            Validates that the requests request is configured correctly and has the appropriate headers.
        """
        with HTTMock(self.mock_api_response):
            self.pd_client.get(self.TEST_REQUEST_PATH)

        for k, v in self.BASE_HEADERS.items():
            assert k in self.current_request.headers

            actual_value = self.current_request.headers[k]
            assert v == self.current_request.headers[k], self.ASSERTION_EQ_MSG.format(v, actual_value)

        assert 'GET' == self.current_request.method

    def test_post(self):
        """
            Tests the PokitDok.post convenience method.
            Validates that the requests request is configured correctly and has the appropriate headers.
        """
        with HTTMock(self.mock_api_response):
            self.pd_client.post(self.TEST_REQUEST_PATH, data={'field': 'value'})

        for k, v in self.JSON_HEADERS.items():
            assert k in self.current_request.headers

            actual_value = self.current_request.headers[k]
            assert v == self.current_request.headers[k], self.ASSERTION_EQ_MSG.format(v, actual_value)

        assert 'POST' == self.current_request.method

    def test_put(self):
        """
            Tests the PokitDok.put convenience method.
            Validates that the requests request is configured correctly and has the appropriate headers.
        """
        with HTTMock(self.mock_api_response):
            url = '{0}/{1}'.format(self.TEST_REQUEST_PATH, 123456)
            self.pd_client.put(url, data={'first_name': 'Oscar', 'last_name': 'Whitmire'})

        for k, v in self.JSON_HEADERS.items():
            assert k in self.current_request.headers

            actual_value = self.current_request.headers[k]
            assert v == self.current_request.headers[k], self.ASSERTION_EQ_MSG.format(v, actual_value)

        assert 'PUT' == self.current_request.method

    def test_delete(self):
        """
            Tests the PokitDok.delete convenience method.
            Validates that the requests request is configured correctly and has the appropriate headers.
        """
        with HTTMock(self.mock_api_response):
            url = '{0}/{1}'.format(self.TEST_REQUEST_PATH, 123456)
            self.pd_client.delete(url)

        for k, v in self.BASE_HEADERS.items():
            assert k in self.current_request.headers

            actual_value = self.current_request.headers[k]
            assert v == self.current_request.headers[k], self.ASSERTION_EQ_MSG.format(v, actual_value)

        assert 'DELETE' == self.current_request.method

    def test_activities(self):
        """
            Tests PokitDok.activities.
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.activities()
        assert mocked_response is not None

    def test_activities_with_activity_id(self):
        """
            Tests PokitDok.activities with a specific activity id
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.activities('activity_id')
        assert mocked_response is not None 

    def test_cash_prices(self):
        """
            Tests PokitDok.cash_prices
\        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.cash_prices(zip_code='94101', cpt_code='95017')
        assert mocked_response is not None 

    def test_ccd(self):
        """
            Tests PokitDok.ccd
\        """
        with HTTMock(self.mock_api_response):
            ccd_request = {'trading_partner_id': 'MOCKPAYER'}
            mocked_response = self.pd_client.ccd(ccd_request)
        assert mocked_response is not None 

    def test_claims(self):
        """
            Tests PokitDok.claims
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.claims(tests.claim_request)
        assert mocked_response is not None 

    def test_claims_status(self):
        """
            Tests PokitDok.claims_status
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.claims_status(tests.claim_status_request)
        assert mocked_response is not None

    def test_mpc_code_lookup(self):
        """
            Tests PokitDok.mpc (medical procedure code) lookup for a specific code
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.mpc(code='99213')
        assert mocked_response is not None

    def test_mpc_query(self):
        """
            Tests PokitDok.mpc (medical procedure code) query
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.mpc(name='office')
        assert mocked_response is not None 

    def test_icd_convert(self):
        """
            Tests PokitDok.icd_convert
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.icd_convert(code='250.12')
        assert mocked_response is not None 

    def test_claims_convert(self):
        """
            Tests PokitDok.claims_convert
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.icd_convert(tests.claims_convert_request)
        assert mocked_response is not None 

    def test_eligibility(self):
        """
            Tests PokitDok.eligibility
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.eligibility(tests.eligibility_request)
        assert mocked_response is not None 

    def test_enrollment(self):
        """
            Tests PokitDok.enrollment
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.enrollment(tests.enrollment_request)
        assert mocked_response is not None 

    def test_enrollment_snapshot(self):
        """
            Tests PokitDok.enrollment_snapshot
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.enrollment_snapshot(**tests.enrollment_snapshot_request)
        assert mocked_response is not None 

    def test_enrollment_snapshots(self):
        """
            Tests PokitDok.enrollment_snapshots
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.enrollment_snapshots(snapshot_id='12345')
        assert mocked_response is not None 

    def test_enrollment_snapshot_data(self):
        """
            Tests PokitDok.enrollment_snapshot_data
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.enrollment_snapshot_data(snapshot_id='12345')
        assert mocked_response is not None 

    def test_files(self):
        """
            Tests PokitDok.files
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.files(**tests.files_request)
        assert mocked_response is not None 

    def test_insurance_prices(self):
        """
            Tests PokitDok.insurance_prices
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.insurance_prices(cpt_code='87799', zip_code='32218')
        assert mocked_response is not None 

    def test_payers(self):
        """
            Tests PokitDok.payers
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.payers()
        assert mocked_response is not None 

    def test_plans(self):
        """
            Tests PokitDok.plans
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.plans()
        assert mocked_response is not None 

    def test_plans_by_state_type(self):
        """
            Tests PokitDok.plans lookup with state and plan type criteria
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.plans(state='SC', type='PPO')
        assert mocked_response is not None 

    def test_providers_npi(self):
        """
            Tests PokitDok.providers lookup by NPI
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.providers(npi='1467560003')
        assert mocked_response is not None 

    def test_providers_search(self):
        """
            Tests PokitDok.providers search by zipcode, specialty, and radius
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.providers(zipcode='29307',
                                                       specialty='rheumatology',
                                                       radius='20mi')
        assert mocked_response is not None 

    def test_trading_partners(self):
        """
            Tests PokitDok.trading_partners
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.trading_partners()
        assert mocked_response is not None 

    def test_trading_partners_trading_partner_id(self):
        """
            Tests PokitDok.trading_partners lookup by trading_partner_id
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.trading_partners(trading_partner_id='MOCKPAYER')
        assert mocked_response is not None 

    def test_referrals(self):
        """
            Tests PokitDok.referrals
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.referrals(tests.referrals_request)
        assert mocked_response is not None 

    def test_authorizations(self):
        """
            Tests PokitDok.authorizations
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.authorizations(tests.authorization_request)
        assert mocked_response is not None 

    def test_schedulers(self):
        """
            Tests PokitDok.schedulers
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.schedulers()
        assert mocked_response is not None 

    def test_schedulers_with_scheduler_uuid(self):
        """
            Tests PokitDok.schedulers lookup for a specific resource
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.schedulers(scheduler_uuid='967d207f-b024-41cc-8cac-89575a1f6fef')
        assert mocked_response is not None 

    def test_appointment_types(self):
        """
            Tests PokitDok.appointment_types
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.appointment_types()
        assert mocked_response is not None 

    def test_appointment_types_with_appointment_type_uuid(self):
        """
            Tests PokitDok.schedulers lookup for a specific resource
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.appointment_types(
                appointment_type_uuid='ef987693-0a19-447f-814d-f8f3abbf4860')
        assert mocked_response is not None 

    def test_schedule_slots(self):
        """
            Tests PokitDok.schedule_slots
        :return:
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.schedule_slots(tests.slot_create_request)
        assert mocked_response is not None 

    def test_appointments_with_appointment_uuid(self):
        """
            Tests PokitDok.appointments lookup for a specific resource
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.appointments(appointment_uuid='ef987691-0a19-447f-814d-f8f3abbf4859')
        assert mocked_response is not None 

    def test_appointments_with_search(self):
        """
            Tests PokitDok.appointments lookup using search criteria: appointment_type, start_date, and end_date
        """
        with HTTMock(self.mock_api_response):
            search_criteria = {
                'appointment_type': 'AT1',
                'start_date': datetime.date(2016, month=1, day=15),
                'end_date': datetime.date(2016, month=1, day=20),
            }
            mocked_response = self.pd_client.appointments(**search_criteria)
        assert mocked_response is not None 

    def test_book_appointment(self):
        """
            Tests PokitDok.book_appointment
\        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.book_appointment('ef987691-0a19-447f-814d-f8f3abbf4859',
                                                              tests.appointment_book_request)
        assert mocked_response is not None 

    def test_cancel_appointment(self):
        """
            Tests PokitDok.cancel_appointment
\        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.cancel_appointment(appointment_uuid='ef987691-0a19-447f-814d-f8f3abbf4859')
        assert mocked_response is not None 

    def test_create_identity(self):
        """
            Tests PokitDok.create_identity
\        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.create_identity(tests.identity_request)
        assert mocked_response is not None 

    def test_identity_with_uuid(self):
        """
            Tests PokitDok.identity lookup for a specific resource
\        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.identity(identity_uuid='881bc095-2068-43cb-9783-cce63036412')
        assert mocked_response is not None 

    def test_identity_search(self):
        """
            Tests PokitDok.identity with search criteria of first_name and last_name
\        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.identity(first_name='Oscar', last_name='Whitmire')
        assert mocked_response is not None 

    def test_update_identity(self):
        """
            Tests PokitDok.create_identity
\        """
        with HTTMock(self.mock_api_response):
            updated_request = copy.deepcopy(tests.identity_request)
            updated_request['email'] = 'oscar@yahoo.com'

            mocked_response = self.pd_client.update_identity(identity_uuid='881bc095-2068-43cb-9783-cce63036412',
                                                             identity_request=updated_request)
        assert mocked_response is not None 

    def test_identity_history_with_uuid(self):
        """
            Tests PokitDok.identity_history lookup to return a change summary for a specific resource
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.identity_history(identity_uuid='881bc095-2068-43cb-9783-cce63036412')
        assert mocked_response is not None 

    def test_identity_history_with_uuid_version(self):
        """
            Tests PokitDok.identity_history lookup for a version of a specific resource
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.identity_history(identity_uuid='881bc095-2068-43cb-9783-cce63036412',
                                                              historical_version=1)
        assert mocked_response is not None 

    def test_pharmacy_plans(self):
        """
            Tests PokitDok.pharmacy_plans
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.pharmacy_plans(trading_partner_id='MOCKPAYER', plan_number='S5820003')
        assert mocked_response is not None 

    def test_pharmacy_formulary(self):
        """
            Tests PokitDok.pharmacy_formulary
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.pharmacy_formulary(trading_partner_id='MOCKPAYER', plan_number='S5820003',
                                                                ndc='59310-579-22')
        assert mocked_response is not None 

    def test_pharmacy_drug_cost(self):
        """
            Tests PokitDok.pharmacy_drug_cost
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.pharmacy_drug_cost(trading_partner_id='MOCKPAYER', plan_number='S5820003',
                                                                ndc='59310-579-22')
        assert mocked_response is not None

    def test_pharmacy_network_by_npi(self):
        """
            Tests PokitDok.pharmacy_network by NPI
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.pharmacy_network(trading_partner_id='MOCKPAYER', plan_number='S5596033',
                                                                npi='1912301953')
        assert mocked_response is not None

    def test_pharmacy_network_search(self):
        """
            Tests PokitDok.pharmacy_network search
        """
        with HTTMock(self.mock_api_response):
            mocked_response = self.pd_client.pharmacy_network(trading_partner_id='MOCKPAYER', plan_number='S5596033',
                                                                zipcode='94401', radius='10mi')
        assert mocked_response is not None
