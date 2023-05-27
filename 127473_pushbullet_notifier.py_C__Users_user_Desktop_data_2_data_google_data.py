import pushbullet

from graphitepager.notifiers.base import BaseNotifier


class PushBulletNotifier(BaseNotifier):

    def __init__(self, storage, config, client=None):
        super(PushBulletNotifier, self).__init__(storage, config)
        self._devices = set()
        self._contacts = set()

        required = ['PUSHBULLET_KEY']
        self.enabled = config.has_keys(required)
        if self.enabled:
            self._client = \
                client or pushbullet.PushBullet(config.get('PUSHBULLET_KEY'))

            devices = config.get("PUSHBULLET_DEVICES")
            for device in (devices and devices.split(",") or []):
                self.add_device(device.strip())

            contacts = config.get("PUSHBULLET_CONTACTS")
            for contact in (contacts and contacts.split(",") or []):
                self.add_contact(contact.strip())

    def _notify(self,
                alert,
                level,
                description,
                nominal=None):

        self._notify_clients_with_args(
            "[%s]: %s" % (level, alert.get("name")),
            description.graphite_url,
            str(description)
        )

    def _notify_clients_with_args(self, title, url, description):
        if not self._devices:
            self._client.push_link(title, url, body=description)
        else:
            for device in self._client.devices:
                if device.device_iden in self._devices:
                    device.push_link(title, url, body=description)

        for contact in self._client.contacts:
            if contact.email in self._contacts:
                contact.push_link(title, url, body=description)

    def add_device(self, device):
        self._devices.add(device)

    def add_contact(self, contact):
        self._contacts.add(contact)
