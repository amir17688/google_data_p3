# Copyright 2013 Rackspace
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__all__ = [
    'for_all_regions'
]

import os

from raxcli.commands import BaseCommand, BaseListCommand
from raxcli.config import get_config as get_base_config
from raxcli.apps.utils import for_all_regions as base_get_all_regions
from raxcli.apps.loadbalancer.constants import SERVICE_CATALOG_ENTRY_NAME


from libcloud.loadbalancer.providers import get_driver
from libcloud.loadbalancer.types import Provider

import libcloud.security

CA_CERT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            '../data/cacert.pem')
libcloud.security.CA_CERTS_PATH.insert(0, CA_CERT_PATH)


class LoadBalancerCommand(BaseCommand):
    def get_parser(self, prog_name):
        parser = super(LoadBalancerCommand, self).\
            get_parser(prog_name=prog_name)
        parser.add_argument('--auth-url', dest='auth_url')
        parser.add_argument('--region', dest='region')
        return parser


class LoadBalancerBalancerListCommand(LoadBalancerCommand, BaseListCommand):
    def get_parser(self, prog_name):
        parser = super(LoadBalancerBalancerListCommand, self).\
            get_parser(prog_name=prog_name)
        parser.add_argument('--balancer-id', dest='balancer_id', required=True)
        return parser


def get_config():
    return get_base_config(app='loadbalancer')


def get_client(parsed_args, driver_kwargs=None):
    config = get_config()
    # TODO: regions/uk
    driver = get_driver(Provider.RACKSPACE_US)

    username = config['username']
    api_key = config['api_key']
    if parsed_args.username:
        username = parsed_args.username
    if parsed_args.api_key:
        api_key = parsed_args.api_key

    api_url = parsed_args.api_url
    auth_url = parsed_args.auth_url

    if not username:
        raise ValueError('Missing required argument: username')

    if not api_key:
        raise ValueError('Missing required argument: api-key')

    if driver_kwargs:
        options = driver_kwargs.copy()
    else:
        options = {}

    if api_url is not None:
        options['ex_force_base_url'] = api_url

    if auth_url is not None:
        options['ex_force_auth_url'] = auth_url

    if parsed_args.region is not None:
        options['ex_force_region'] = parsed_args.region

    return driver(username, api_key, **options)


def for_all_regions(action_func, parsed_args):
    return base_get_all_regions(get_client_func=get_client,
                                catalog_entry=SERVICE_CATALOG_ENTRY_NAME,
                                action_func=action_func,
                                parsed_args=parsed_args)
