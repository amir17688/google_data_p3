# -*- coding: utf-8 -*-

#    Copyright 2015 Mirantis, Inc.
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

from netaddr import IPNetwork

from nailgun import consts
from nailgun.db import db
from nailgun.db.sqlalchemy import models
from nailgun import errors
from nailgun.extensions.network_manager.objects.serializers.network_group \
    import NetworkGroupSerializer
from nailgun.logger import logger
from nailgun.objects import Cluster
from nailgun.objects import NailgunCollection
from nailgun.objects import NailgunObject

from sqlalchemy.sql import or_


class NetworkGroup(NailgunObject):

    model = models.NetworkGroup
    serializer = NetworkGroupSerializer

    @classmethod
    def fields(cls):
        return cls.model.__mapper__.columns.keys() + ["meta"]

    @classmethod
    def get_from_node_group_by_name(cls, node_group_id, network_name):
        return db().query(models.NetworkGroup).filter_by(
            group_id=node_group_id, name=network_name).first()

    @classmethod
    def get_default_admin_network(cls):
        return db().query(models.NetworkGroup).filter_by(
            group_id=None, name=consts.NETWORKS.fuelweb_admin).first()

    @classmethod
    def get_by_node_group(cls, node_group_id):
        """Get all non-admin networks belonging to specified node group.

        :param node_group_id: NodeGroup ID
        :type node_group_id: int
        :returns: list of NetworkGroup instances
        """
        return db().query(models.NetworkGroup).filter_by(
            group_id=node_group_id,
        ).filter(
            models.NetworkGroup.name != consts.NETWORKS.fuelweb_admin
        ).order_by(models.NetworkGroup.id).all()

    @classmethod
    def get_admin_network_group(cls, node=None, default_admin_net=None):
        """Method for receiving Admin NetworkGroup.

        :param node: return admin network groupd of this node
        :type node: nailgun.db.sqlalchemy.models.Node
        :param default_admin_net: Default admin network
        :param nailgun.db.sqlalchemy.models.NetworkGroup
        :returns: Admin NetworkGroup.
        :raises: errors.AdminNetworkNotFound
        """
        network = None

        if node is not None and node.nodegroup:
            networks = (network for network in node.nodegroup.networks
                        if network.name == consts.NETWORKS.fuelweb_admin)
            network = next(networks, None)

        network = (network or default_admin_net or
                   cls.get_default_admin_network())

        if not network:
            raise errors.AdminNetworkNotFound()
        return network

    @classmethod
    def get_assigned_ips(cls, network_id):
        """Get all IPs assigned to specified network group.

        :param network_id: NetworkGroup ID
        :type network_id: int
        :returns: list of IPAddr instances
        """
        ips = [
            x[0] for x in db().query(
                models.IPAddr.ip_addr
            ).filter(
                models.IPAddr.network == network_id,
                or_(
                    models.IPAddr.node.isnot(None),
                    models.IPAddr.vip_name.isnot(None)
                )
            )]

        return ips

    @classmethod
    def create(cls, data):
        """Create NetworkGroup instance with specified parameters in DB.

        Create corresponding IPAddrRange instance with IP range specified in
        data or calculated from CIDR if not specified.

        :param data: dictionary of key-value pairs as NetworkGroup fields
        :returns: instance of new NetworkGroup
        """
        instance = super(NetworkGroup, cls).create(data)
        cls._create_ip_ranges_on_notation(instance)
        cls._reassign_template_networks(instance)
        db().refresh(instance)
        return instance

    @classmethod
    def update(cls, instance, data):
        # cleanup stalled data and generate new for the group
        cls._regenerate_ip_ranges_on_notation(instance, data)

        # as ip ranges were regenerated we must update instance object
        # in order to prevent possible SQAlchemy errors with operating
        # on stale data
        db().refresh(instance)

        # remove 'ip_ranges' (if) any from data as this is relation
        # attribute for the orm model object
        data.pop('ip_ranges', None)
        return super(NetworkGroup, cls).update(instance, data)

    @classmethod
    def delete(cls, instance):
        notation = instance.meta.get('notation')
        if notation and not instance.nodegroup.cluster.is_locked:
            cls._delete_ips(instance)
        instance.nodegroup.networks.remove(instance)
        db().flush()

    @classmethod
    def is_untagged(cls, instance):
        """Return True if network is untagged"""
        return (instance.vlan_start is None) \
            and not instance.meta.get('neutron_vlan_range') \
            and not instance.meta.get('ext_net_data')

    @classmethod
    def get_by_cluster(cls, cluster_id):
        """Get network groups for all node groups in specified cluster.

        :param cluster_id: Cluster ID
        :type cluster_id: int
        :return: Network groups for all node groups in cluster
        """
        return db().query(
            models.NetworkGroup.id,
            models.NetworkGroup.name,
            models.NetworkGroup.meta,
        ).join(
            models.NetworkGroup.nodegroup
        ).filter(
            models.NodeGroup.cluster_id == cluster_id,
            models.NetworkGroup.name != consts.NETWORKS.fuelweb_admin
        )

    @classmethod
    def _create_ip_ranges_on_notation(cls, instance):
        """Create IP-address ranges basing on 'notation' field of 'meta' field

        :param instance: NetworkGroup instance
        :type instance: models.NetworkGroup
        :return: None
        """
        notation = instance.meta.get("notation")
        if notation:
            try:
                if notation == 'cidr':
                    cls._update_range_from_cidr(
                        instance, IPNetwork(instance.cidr).cidr,
                        instance.meta.get('use_gateway'))
                elif notation == 'ip_ranges' and instance.meta.get("ip_range"):
                    cls._set_ip_ranges(instance, [instance.meta["ip_range"]])
                else:
                    raise errors.CannotCreate()
            except (
                errors.CannotCreate,
                IndexError,
                TypeError
            ):
                raise errors.CannotCreate(
                    "IPAddrRange object cannot be created for network '{0}' "
                    "with notation='{1}', ip_range='{2}'".format(
                        instance.name,
                        instance.meta.get('notation'),
                        instance.meta.get('ip_range'))
                )

    @classmethod
    def _regenerate_ip_ranges_on_notation(cls, instance, data):
        """Regenerate IP-address ranges

        This method regenerates IPs based on 'notation' field of
        Network group 'meta' content.

        :param instance: NetworkGroup instance
        :type instance: models.NetworkGroup
        :param data: network data
        :type data: dict
        :return: None
        """
        notation = instance.meta['notation']
        data_meta = data.get('meta', {})

        notation = data_meta.get('notation', notation)
        if notation == consts.NETWORK_NOTATION.ip_ranges:
            ip_ranges = data.get("ip_ranges") or \
                [(r.first, r.last) for r in instance.ip_ranges]
            cls._set_ip_ranges(instance, ip_ranges)

        elif notation == consts.NETWORK_NOTATION.cidr:
            use_gateway = data_meta.get(
                'use_gateway', instance.meta.get('use_gateway'))
            cidr = data.get('cidr', instance.cidr)
            cls._update_range_from_cidr(
                instance, cidr, use_gateway=use_gateway)

    @classmethod
    def _set_ip_ranges(cls, instance, ip_ranges):
        """Set IP-address ranges.

        :param instance: NetworkGroup instance being updated
        :type instance: models.NetworkGroup
        :param ip_ranges: IP-address ranges sequence
        :type ip_ranges: iterable of pairs
        :return: None
        """
        # deleting old ip ranges
        db().query(models.IPAddrRange).filter_by(
            network_group_id=instance.id).delete()

        for r in ip_ranges:
            new_ip_range = models.IPAddrRange(
                first=r[0],
                last=r[1],
                network_group_id=instance.id)
            db().add(new_ip_range)
        db().refresh(instance)
        db().flush()

    @classmethod
    def _update_range_from_cidr(
            cls, instance, cidr, use_gateway=False):
        """Update network ranges for CIDR.

        :param instance: NetworkGroup instance being updated
        :type instance: models.NetworkGroup
        :param cidr: CIDR network representation
        :type cidr: basestring
        :param use_gateway: whether gateway is taken into account
        :type use_gateway: bool
        :return: None
        """
        first_idx = 2 if use_gateway else 1
        new_cidr = IPNetwork(cidr)
        ip_range = (str(new_cidr[first_idx]), str(new_cidr[-2]))
        cls._set_ip_ranges(instance, [ip_range])

    @classmethod
    def _delete_ips(cls, instance):
        """Network group cleanup

        Deletes all IPs which were assigned within the network group.

        :param instance: NetworkGroup instance
        :type  instance: models.NetworkGroup
        :returns: None
        """
        logger.debug("Deleting old IPs for network with id=%s, cidr=%s",
                     instance.id, instance.cidr)
        db().query(models.IPAddr).filter(
            models.IPAddr.network == instance.id
        ).delete()
        db().flush()

    @classmethod
    def _reassign_template_networks(cls, instance):
        cluster = instance.nodegroup.cluster
        if not cluster.network_config.configuration_template:
            return

        nm = Cluster.get_network_manager(cluster)
        for node in cluster.nodes:
            nm.assign_networks_by_template(node)

    @classmethod
    def get_node_network_by_name(cls, node, network_name,
                                 default_admin_net=None):
        """Find a network with given name, to which a node is connected.

        :param node: node, which is connected to a network
        :type node: nailgun.db.sqlalchemy.models.Node
        :param network_name: Name of the network
        :type network_name: str
        :param default_admin_net: if fuelweb_admin network is
         requested and node doen't have custom admin network,
         then this one will be returned (it's may be provided
         for performance reasons)
        :return: nailgun.db.sqlalchemy.models.NetworkGroup
        """
        if network_name == consts.NETWORKS.fuelweb_admin:
            return cls.get_admin_network_group(node, default_admin_net)
        else:
            return cls.get_from_node_group_by_name(node.group_id, network_name)

    @classmethod
    def get_network_by_name_and_nodegroup(cls, name, nodegroup):
        """Find a network that matches a specified name and a nodegroup.

        :param name: Name of a network
        :param nodegroup: The nodegroup object
        :return: Network object that matches a specified name and a nodegroup.
                 Admin network, if nothing found.

        """
        network = cls.get_from_node_group_by_name(nodegroup.id, name)

        # FIXME:
        #   Built-in fuelweb_admin network doesn't belong to any node
        #   group, since it's shared between all clusters. So we need
        #   to handle this very special case if we want to be able
        #   to allocate VIP in default admin network.
        if not network and name == consts.NETWORKS.fuelweb_admin:
            network = cls.get_default_admin_network()

        return network


class NetworkGroupCollection(NailgunCollection):

    single = NetworkGroup
