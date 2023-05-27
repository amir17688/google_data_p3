#!/usr/bin/env python

"""
JSON misc commands plugin
"""

try:
    import anyjson
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        import json

    class anyjson(object):
        """Fake anyjson module as a class"""

        @staticmethod
        def serialize(buf):
            return json.dumps(buf)

        @staticmethod
        def deserialize(buf):
            return json.loads(buf)


import os
import platform
import pyxenstore


XENSTORE_INTERFACE_PATH = "vm-data/networking"
XENSTORE_HOSTNAME_PATH = "vm-data/hostname"
XENSTORE_VIRT_PROVIDER = "vm-data/allowvssprovider"
XENSTORE_USER_METADATA = "vm-data/user-metadata"
XENSTORE_AUTO_DISK_CONFIG = "vm-data/auto-disk-config"

DEFAULT_HOSTNAME = ''


def recon():
    system = os.uname()[0]
    if system == "Linux":
        system = platform.linux_distribution(full_distribution_name=0)[0]

        # Arch Linux returns None for platform.linux_distribution()
        if not system and os.path.exists('/etc/arch-release'):
            system = 'arch'

    if not system:
        return None

    system = system.lower()
    global DEFAULT_HOSTNAME
    DEFAULT_HOSTNAME = system


def read_xenstore():
    recon()
    xs_handle = pyxenstore.Handle()

    try:
        hostname = xs_handle.read(XENSTORE_HOSTNAME_PATH)
        print('hostname: %r (from xenstore)\n' % hostname)
    except pyxenstore.NotFoundError:
        hostname = DEFAULT_HOSTNAME
        print('hostname: %r (DEFAULT)\n' % hostname)

    interfaces = []

    try:
        entries = xs_handle.entries(XENSTORE_INTERFACE_PATH)
    except pyxenstore.NotFoundError:
        entries = []

    for entry in entries:
        data = xs_handle.read(XENSTORE_INTERFACE_PATH + '/' + entry)
        data = anyjson.deserialize(data)
        interfaces.append(data)
        print('interface %s: %r\n' % (entry, data))

    del xs_handle


if __name__ == "__main__":
    read_xenstore()
