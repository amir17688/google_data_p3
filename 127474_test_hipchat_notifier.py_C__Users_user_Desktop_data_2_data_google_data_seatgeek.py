from unittest import TestCase

from mock import MagicMock
from hipchat import HipChat


from graphitepager.description import Description
from graphitepager.notifiers.hipchat_notifier import HipChatNotifier
from graphitepager.redis_storage import RedisStorage
from graphitepager.alerts import Alert
from graphitepager.config import Config
from graphitepager.level import Level


class TestHipChatNotifier(TestCase):

    def setUp(self):
        self.alert_key = 'ALERT KEY'
        self.description = MagicMock(Description)
        self.mock_config = MagicMock(Config)
        self.mock_redis_storage = MagicMock(RedisStorage)
        self.mock_hipchat_client = MagicMock(HipChat)
        self.mock_alert = MagicMock(Alert)

        self.mock_config.get = self.mock_get

        self.hcn = HipChatNotifier(self.mock_redis_storage, self.mock_config)
        self.hcn._client = self.mock_hipchat_client

    def mock_get(self, key, default=None):
        if key == 'HIPCHAT_KEY':
            return 'HIPCHAT_KEY'
        if key == 'HIPCHAT_ROOM':
            return 'ROOM NAME'
        return default

    def test_should_not_notify_hipchat_if_no_rooms_have_been_added(self):
        self.hcn.notify(
            self.mock_alert,
            self.alert_key,
            Level.WARNING,
            self.description)

        self.assertEqual(self.mock_hipchat_client.message_room.mock_calls, [])

    def test_should_not_notify_hipchat_if_warning_and_already_notified(self):
        self.mock_redis_storage.is_locked_for_domain_and_key.\
            return_value = True

        self.hcn.notify(
            self.mock_alert,
            self.alert_key,
            Level.WARNING,
            self.description)

        self.assertEqual(self.mock_hipchat_client.mock_calls, [])

    def test_should_notify_hipchat_resolved_if_nominal_and_had_notified(self):
        room_name = 'ROOM NAME'
        self.hcn.add_room(room_name)
        self.mock_redis_storage.is_locked_for_domain_and_key.\
            return_value = True

        self.hcn.notify(
            self.mock_alert,
            self.alert_key,
            Level.NOMINAL,
            self.description)

        self.mock_redis_storage.is_locked_for_domain_and_key.\
            assert_called_once_with('HipChat', self.alert_key)
        self.mock_hipchat_client.message_room.assert_called_once_with(
            room_name,
            'Graphite-Pager',
            self.description.html(),
            message_format='html',
            color='green',
        )
        self.mock_redis_storage.remove_lock_for_domain_and_key.\
            assert_called_once_with('HipChat', self.alert_key)

    def test_should_notify_room_of_warning_if_had_not_notified_before(self):
        room_name = 'ROOM NAME'
        self.hcn.add_room(room_name)
        self.mock_redis_storage.is_locked_for_domain_and_key.\
            return_value = False

        self.hcn.notify(
            self.mock_alert,
            self.alert_key,
            Level.WARNING,
            self.description)

        self.mock_hipchat_client.message_room.assert_called_once_with(
            room_name,
            'Graphite-Pager',
            self.description.html(),
            message_format='html',
            color='yellow'
        )
        self.mock_redis_storage.set_lock_for_domain_and_key.\
            assert_called_once_with('HipChat', self.alert_key)

    def test_should_notify_room_of_critical_if_had_not_notified_before(self):
        room_name = 'ROOM NAME'
        self.hcn.add_room(room_name)
        self.mock_redis_storage.is_locked_for_domain_and_key.\
            return_value = False

        self.hcn.notify(
            self.mock_alert,
            self.alert_key,
            Level.CRITICAL,
            self.description)

        self.mock_hipchat_client.message_room.assert_called_once_with(
            room_name,
            'Graphite-Pager',
            self.description.html(),
            message_format='html',
            color='red'
        )
        self.mock_redis_storage.set_lock_for_domain_and_key.\
            assert_called_once_with('HipChat', self.alert_key)

    def test_should_notify_room_of_no_data_if_had_not_notified_before(self):
        room_name = 'ROOM NAME'
        self.hcn.add_room(room_name)
        self.mock_redis_storage.is_locked_for_domain_and_key.\
            return_value = False

        self.hcn.notify(
            self.mock_alert,
            self.alert_key,
            Level.NO_DATA,
            self.description)

        self.mock_hipchat_client.message_room.assert_called_once_with(
            room_name,
            'Graphite-Pager',
            self.description.html(),
            message_format='html',
            color='red'
        )
        self.mock_redis_storage.set_lock_for_domain_and_key.\
            assert_called_once_with('HipChat', self.alert_key)
