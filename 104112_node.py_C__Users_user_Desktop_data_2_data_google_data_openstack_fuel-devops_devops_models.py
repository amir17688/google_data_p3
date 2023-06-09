#    Copyright 2013 - 2016 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django.conf import settings
from django.db import models
from django.utils.functional import cached_property

from devops.error import DevopsError
from devops.helpers.helpers import tcp_ping_
from devops.helpers.helpers import wait_pass
from devops.helpers.helpers import wait_ssh_cmd
from devops.helpers.helpers import wait_tcp
from devops.helpers import loader
from devops.helpers.ssh_client import SSHClient
from devops import logger
from devops.models.base import BaseModel
from devops.models.base import ParamedModel
from devops.models.base import ParamField
from devops.models.network import Interface
from devops.models.network import NetworkConfig
from devops.models.volume import DiskDevice


class Node(ParamedModel, BaseModel):
    class Meta(object):
        unique_together = ('name', 'group')
        db_table = 'devops_node'
        app_label = 'devops'

    group = models.ForeignKey('Group', null=True)
    name = models.CharField(max_length=255, unique=False, null=False)
    role = models.CharField(max_length=255, null=True)

    kernel_cmd = ParamField()
    ssh_port = ParamField(default=22)
    bootstrap_timeout = ParamField(default=600)
    deploy_timeout = ParamField(default=3600)
    deploy_check_cmd = ParamField()

    @property
    def driver(self):
        drv = self.group.driver

        # LEGACY (fuel-qa compatibility requires), TO REMOVE
        def node_active(node):
            return node.is_active()
        drv.node_active = node_active

        return drv

    @cached_property
    def ext(self):
        ExtCls = loader.load_class(
            'devops.models.node_ext.{ext_name}:NodeExtension'
            ''.format(ext_name=self.role or 'default'))
        return ExtCls(node=self)

    def define(self, *args, **kwargs):
        self.save()

    def start(self, *args, **kwargs):
        pass

    def destroy(self, *args, **kwargs):
        pass

    def erase(self, *args, **kwargs):
        self.remove()

    def remove(self, *args, **kwargs):
        self.erase_volumes()
        self.delete()

    def suspend(self, *args, **kwargs):
        pass

    def resume(self, *args, **kwargs):
        pass

    def snapshot(self, *args, **kwargs):
        pass

    def revert(self, *args, **kwargs):
        pass

    # for fuel-qa compatibility
    def has_snapshot(self, *args, **kwargs):
        return True

    # for fuel-qa compatibility
    def get_snapshots(self):
        """Return full snapshots objects"""
        return []

    @property
    def disk_devices(self):
        return self.diskdevice_set.all()

    @property
    def interfaces(self):
        return self.interface_set.order_by('id')

    @property
    def network_configs(self):
        return self.networkconfig_set.all()

    # LEGACY, for fuel-qa compatibility
    @property
    def is_admin(self):
        return self.role.startswith('fuel_master')

    # LEGACY, for fuel-qa compatibility
    @property
    def is_slave(self):
        return self.role == 'fuel_slave'

    def next_disk_name(self):
        disk_names = ('sd' + c for c in list('abcdefghijklmnopqrstuvwxyz'))
        for disk_name in disk_names:
            if not self.disk_devices.filter(target_dev=disk_name).exists():
                return disk_name

    # TODO(astudenov): LEGACY, TO REMOVE
    def interface_by_network_name(self, network_name):
        logger.warning('interface_by_network_name is deprecated in favor of '
                       'get_interface_by_network_name')
        raise DeprecationWarning(
            "'Node.interface_by_network_name' is deprecated. "
            "Use 'Node.get_interface_by_network_name' instead.")

    def get_interface_by_network_name(self, network_name):
        return self.interface_set.get(
            l2_network_device__name=network_name)

    def get_interface_by_nailgun_network_name(self, name):
        for net_conf in self.networkconfig_set.all():
            if name in net_conf.networks:
                label = net_conf.label
                break
        else:
            return None
        return self.interface_set.get(label=label)

    def get_ip_address_by_network_name(self, name, interface=None):
        interface = interface or self.interface_set.filter(
            l2_network_device__name=name).order_by('id')[0]
        return interface.address_set.get(interface=interface).ip_address

    def get_ip_address_by_nailgun_network_name(self, name):
        interface = self.get_interface_by_nailgun_network_name(name)
        return interface.address_set.first().ip_address

    def remote(self, network_name, login, password=None, private_keys=None):
        """Create SSH-connection to the network

        :rtype : SSHClient
        """
        return SSHClient(
            self.get_ip_address_by_network_name(network_name),
            username=login,
            password=password, private_keys=private_keys)

    def await(self, network_name, timeout=120, by_port=22):
        wait_pass(
            lambda: tcp_ping_(
                self.get_ip_address_by_network_name(network_name), by_port),
            timeout=timeout)

    # NEW
    def add_interfaces(self, interfaces):
        for interface in interfaces:
            label = interface['label']
            l2_network_device_name = interface.get('l2_network_device')
            interface_model = interface.get('interface_model')
            self.add_interface(
                label=label,
                l2_network_device_name=l2_network_device_name,
                interface_model=interface_model)

    # NEW
    def add_interface(self, label, l2_network_device_name, interface_model):
        if l2_network_device_name:
            env = self.group.environment
            l2_network_device = env.get_env_l2_network_device(
                name=l2_network_device_name)
        else:
            l2_network_device = None

        Interface.interface_create(
            node=self,
            label=label,
            l2_network_device=l2_network_device,
            model=interface_model,
        )

    # NEW
    def add_network_configs(self, network_configs):
        for label, data in network_configs.items():
            self.add_network_config(
                label=label,
                networks=data.get('networks', []),
                aggregation=data.get('aggregation'),
                parents=data.get('parents', []),
            )

    # NEW
    def add_network_config(self, label, networks=None, aggregation=None,
                           parents=None):
        if networks is None:
            networks = []
        if parents is None:
            parents = []
        NetworkConfig.objects.create(
            node=self,
            label=label,
            networks=networks,
            aggregation=aggregation,
            parents=parents,
        )

    # NEW
    def add_volumes(self, volumes):
        for vol_params in volumes:
            self.add_volume(
                **vol_params
            )

    # NEW
    def add_volume(self, name, device='disk', bus='virtio', **params):
        cls = self.driver.get_model_class('Volume')
        volume = cls.objects.create(
            node=self,
            name=name,
            **params
        )
        DiskDevice.node_attach_volume(
            node=self,
            volume=volume,
            device=device,
            bus=bus,
        )
        return volume

    # NEW
    def get_volume(self, **kwargs):
        return self.volume_set.get(**kwargs)

    # NEW
    def get_volumes(self, **kwargs):
        return self.volume_set.filter(**kwargs)

    # NEW
    def erase_volumes(self):
        for volume in self.get_volumes():
            volume.erase()

    def _start_setup(self):
        if self.kernel_cmd is None:
            raise DevopsError('kernel_cmd is None')

        self.start()
        self.send_kernel_keys(self.kernel_cmd)

    def send_kernel_keys(self, kernel_cmd):
        """Provide variables data to kernel cmd format template"""

        ip = self.get_ip_address_by_network_name(
            settings.SSH_CREDENTIALS['admin_network'])
        master_iface = self.get_interface_by_network_name(
            settings.SSH_CREDENTIALS['admin_network'])
        admin_ap = master_iface.l2_network_device.address_pool

        result_kernel_cmd = kernel_cmd.format(
            ip=ip,
            mask=admin_ap.ip_network.netmask,
            gw=admin_ap.gateway,
            hostname=settings.DEFAULT_MASTER_FQDN,
            nameserver=settings.DEFAULT_DNS,
        )
        self.send_keys(result_kernel_cmd)

    def bootstrap_and_wait(self):
        if self.kernel_cmd is None:
            self.kernel_cmd = self.ext.get_kernel_cmd()
            self.save()
        self._start_setup()
        ip = self.get_ip_address_by_network_name(
            settings.SSH_CREDENTIALS['admin_network'])
        wait_tcp(host=ip, port=self.ssh_port,
                 timeout=self.bootstrap_timeout)

    def deploy_wait(self):
        ip = self.get_ip_address_by_network_name(
            settings.SSH_CREDENTIALS['admin_network'])
        if self.deploy_check_cmd is None:
            self.deploy_check_cmd = self.ext.get_deploy_check_cmd()
            self.save()
        wait_ssh_cmd(host=ip,
                     port=self.ssh_port,
                     check_cmd=self.deploy_check_cmd,
                     username=settings.SSH_CREDENTIALS['login'],
                     password=settings.SSH_CREDENTIALS['password'],
                     timeout=self.deploy_timeout)
