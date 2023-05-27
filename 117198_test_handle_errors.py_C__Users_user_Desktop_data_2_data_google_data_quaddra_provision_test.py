import unittest

import libcloud.compute.types
import libcloud.compute.base

import provision.config as config

class TestHandleErrors(unittest.TestCase):

    def setUp(self):
        self.devnull = open('/dev/null', 'w')
        self.node = libcloud.compute.base.Node(1, 'testnode', None, None, None, None)
        self.driver = object()

    def tearDown(self):
        self.devnull.close()

    def test_simple_success(self):
        assert config.handle_errors(lambda: 0) == 0

    def test_parsed_success(self):
        assert config.handle_errors(lambda parsed: 0, object()) == 0

    def test_simple_fail(self):
        assert config.handle_errors(lambda: 1) == 1

    def test_generic_exception(self):
        def raises():
             raise Exception()
        assert config.handle_errors(raises, out=self.devnull) == config.EXCEPTION

    def test_service_unavailable(self):
        def raises():
             raise libcloud.compute.types.MalformedResponseError(
                 "Failed to parse XML", body='Service Unavailable', driver=self.driver)
        assert config.handle_errors(raises, out=self.devnull) == config.SERVICE_UNAVAILABLE

    def test_malformed_response(self):
        def raises():
             raise libcloud.compute.types.MalformedResponseError(
                 "Failed to parse XML", body='A bad response', driver=self.driver)
        assert config.handle_errors(raises, out=self.devnull) == config.MALFORMED_RESPONSE

    def test_timeout(self):
        def raises():
            try:
                None.open_sftp_client
            except AttributeError as e:
                raise libcloud.compute.types.DeploymentError(self.node, e, driver=self.driver)
        assert config.handle_errors(raises, out=self.devnull) == config.TIMEOUT

    def test_deployment_error(self):
        def raises():
            try:
                None.foo
            except AttributeError as e:
                raise libcloud.compute.types.DeploymentError(self.node, e, driver=self.driver)
        assert config.handle_errors(raises, out=self.devnull) == config.DEPLOYMENT_ERROR
