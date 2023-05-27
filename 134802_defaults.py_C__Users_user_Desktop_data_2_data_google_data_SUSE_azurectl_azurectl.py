# Copyright (c) 2015 SUSE Linux GmbH.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from collections import namedtuple
from pkg_resources import resource_filename

# project
from azurectl_exceptions import AzureDomainLookupError


class Defaults(object):
    """
        Default values and static information
    """
    @classmethod
    def get_azure_domain(self, region):
        """
            return domain name according to the specified Azure region
        """
        azure_domain = {
            'Australia East': 'cloudapp.net',
            'Australia Southeast': 'cloudapp.net',
            'Brazil South': 'cloudapp.net',
            'Central India': 'cloudapp.net',
            'Central US': 'cloudapp.net',
            'East Asia': 'cloudapp.net',
            'East US 2': 'cloudapp.net',
            'East US': 'cloudapp.net',
            'Japan East': 'cloudapp.net',
            'Japan West': 'cloudapp.net',
            'North Central US': 'cloudapp.net',
            'North Europe': 'cloudapp.net',
            'South Central US': 'cloudapp.net',
            'Southeast Asia': 'cloudapp.net',
            'South India': 'cloudapp.net',
            'West Europe': 'cloudapp.net',
            'West India': 'cloudapp.net',
            'West US': 'cloudapp.net',
            'Canada Central': 'cloudapp.net',
            'Canada East': 'cloudapp.net',
            'China North': 'chinacloudapp.cn',
            'China East': 'chinacloudapp.cn',
            'Germany Central': 'azurecloudapp.de',
            'Germany Northeast': 'azurecloudapp.de'
        }
        if region not in azure_domain:
            raise AzureDomainLookupError(
                'Specified region %s not in lookup table' % region
            )
        return azure_domain[region]

    @classmethod
    def project_file(self, filename):
        return resource_filename('azurectl', filename)

    @classmethod
    def account_type_for_docopts(self, docopts, return_default=True):
        for account_type_tuple in self.__get_account_type_tuples():
            selection = account_type_tuple.command
            if selection in docopts and docopts[selection]:
                return account_type_tuple.account_type
        if return_default:
            return 'Standard_GRS'

    @classmethod
    def docopt_for_account_type(self, account_type):
        for account_type_tuple in self.__get_account_type_tuples():
            if account_type_tuple.account_type == account_type:
                return account_type_tuple.command

    @classmethod
    def __get_account_type_tuples(self):
        """
            Maps ASM storage account_type to a backup strategy command
        """
        AccountTypeTuple = namedtuple(
            'AccountTypeTuple',
            'account_type command'
        )
        return [
            AccountTypeTuple(
                account_type='Standard_LRS',
                command='--locally-redundant'
            ),
            AccountTypeTuple(
                account_type='Standard_ZRS',
                command='--zone-redundant'
            ),
            AccountTypeTuple(
                account_type='Standard_GRS',
                command='--geo-redundant'
            ),
            AccountTypeTuple(
                account_type='Standard_RAGRS',
                command='--read-access-geo-redundant'
            )
        ]

    @classmethod
    def host_caching_for_docopts(self, docopts, return_default=True):
        for host_caching_tuple in self.__get_host_caching_tuples():
            if docopts[host_caching_tuple.command]:
                return host_caching_tuple.host_caching
        if return_default:
            return 'ReadOnly'

    @classmethod
    def __get_host_caching_tuples(self):
        """
            Maps ASM DataDisk host_caching to a caching command
        """
        HostCachingTuple = namedtuple(
            'HostCachingTuple',
            'host_caching command'
        )
        return [
            HostCachingTuple(
                host_caching='None',
                command='--no-cache'
            ),
            HostCachingTuple(
                host_caching='ReadOnly',
                command='--read-only-cache'
            ),
            HostCachingTuple(
                host_caching='ReadWrite',
                command='--read-write-cache'
            )
        ]

    @classmethod
    def get_attribute(self, instance, name):
        return getattr(instance, name)

    @classmethod
    def set_attribute(self, instance, name, value):
        return setattr(instance, name, value)
