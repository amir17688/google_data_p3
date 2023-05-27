from unittest import TestCase


from mock import MagicMock
from pagerduty import PagerDuty

from graphitepager.description import Description
from graphitepager.notifiers.pagerduty_notifier import PagerdutyNotifier
from graphitepager.redis_storage import RedisStorage
from graphitepager.alerts import Alert
from graphitepager.config import Config
from graphitepager.level import Level


class TestPagerduteryNotifier(TestCase):

    def setUp(self):
        self.alert_key = 'ALERT KEY'
        self.description = MagicMock(Description)
        self.mock_config = MagicMock(Config)
        self.mock_redis_storage = MagicMock(RedisStorage)
        self.mock_pagerduty_client = MagicMock(PagerDuty)
        self.mock_pagerduty_client.service_key = None
        self.mock_alert = MagicMock(Alert)

        self.pn = PagerdutyNotifier(self.mock_redis_storage, self.mock_config)
        self.pn._client = self.mock_pagerduty_client

    def test_should_trigger_with_warning_level_and_key(self):
        incident_key = 'KEY'
        self.mock_redis_storage.get_incident_key_for_alert_key.\
            return_value = incident_key

        self.pn.notify(
            self.mock_alert,
            self.alert_key,
            Level.WARNING,
            self.description)

        self.mock_redis_storage.get_incident_key_for_alert_key.\
            assert_called_once_with(self.alert_key)
        self.mock_pagerduty_client.trigger.assert_called_once_with(
            incident_key=incident_key, description=str(self.description))
        self.mock_redis_storage.set_incident_key_for_alert_key.\
            assert_called_once_with(
                self.alert_key,
                self.mock_pagerduty_client.trigger())

    def test_should_trigger_with_warning_level_and_no_key(self):
        self.mock_redis_storage.get_incident_key_for_alert_key.\
            return_value = None

        self.pn.notify(
            self.mock_alert,
            self.alert_key,
            Level.WARNING,
            self.description)

        self.mock_redis_storage.get_incident_key_for_alert_key.\
            assert_called_once_with(self.alert_key)
        self.mock_pagerduty_client.trigger.assert_called_once_with(
            incident_key=None, description=str(self.description))
        self.mock_redis_storage.set_incident_key_for_alert_key.\
            assert_called_once_with(
                self.alert_key,
                self.mock_pagerduty_client.trigger())

    def test_should_not_trigger_with_nominal_level_and_no_key(self):
        self.mock_redis_storage.get_incident_key_for_alert_key.\
            return_value = None

        self.pn.notify(
            self.mock_alert,
            self.alert_key,
            Level.NOMINAL,
            self.description)

        self.mock_redis_storage.get_incident_key_for_alert_key.\
            assert_called_once_with(self.alert_key)
        self.assertEqual(self.mock_pagerduty_client.trigger.mock_calls, [])

    def test_should_resolve_with_nominal_level_and_key(self):
        incident_key = 'KEY'
        self.mock_redis_storage.get_incident_key_for_alert_key.\
            return_value = incident_key

        self.pn.notify(
            self.mock_alert,
            self.alert_key,
            Level.NOMINAL,
            self.description)

        self.mock_redis_storage.get_incident_key_for_alert_key.\
            assert_called_once_with(self.alert_key)
        self.mock_pagerduty_client.resolve.\
            assert_called_once_with(incident_key=incident_key)
        self.assertEqual(self.mock_pagerduty_client.trigger.mock_calls, [])
        self.mock_redis_storage.remove_incident_for_alert_key.\
            assert_called_once_with(self.alert_key)
