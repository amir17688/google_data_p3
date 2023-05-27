# Copyright (c) 2016 SUSE.  All rights reserved.
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
# project
from ..storage.container import Container
from ..defaults import Defaults
from ..azurectl_exceptions import (
    AzureStorageAccountCreateError,
    AzureStorageAccountUpdateError,
    AzureStorageAccountDeleteError,
    AzureStorageAccountShowError,
    AzureStorageAccountListError
)


class StorageAccount(object):
    """
        Implements Azure storage account management. This includes the
        following tasks:
        + creation, updates, and deletion of storage accounts
        + listing individual or all storage accounts
    """
    def __init__(self, account):
        self.account = account
        self.service = account.get_management_service()

    def create(self, name, description, label, account_type):
        try:
            result = self.service.create_storage_account(
                name,
                (description or ''),
                (label or name),
                location=self.account.config.get_region_name(),
                account_type=account_type
            )
        except Exception as e:
            raise AzureStorageAccountCreateError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        return result.request_id

    def update(
        self,
        name,
        description,
        label,
        account_type,
        regenerate_primary_key=False,
        regenerate_secondary_key=False
    ):
        try:
            current = self.service.get_storage_account_properties(name)
            self.service.update_storage_account(
                name,
                (description or current.storage_service_properties.description),
                (label or current.storage_service_properties.label),
                account_type=(
                    account_type or
                    current.storage_service_properties.account_type
                )
            )
            if regenerate_primary_key:
                self.service.regenerate_storage_account_keys(name, 'Primary')
            if regenerate_secondary_key:
                self.service.regenerate_storage_account_keys(name, 'Secondary')
        except Exception as e:
            raise AzureStorageAccountUpdateError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        return self.show(name)

    def delete(self, name):
        try:
            result = self.service.delete_storage_account(name)
        except Exception as e:
            raise AzureStorageAccountDeleteError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        return result.request_id

    def exists(self, name):
        try:
            self.service.get_storage_account_properties(name)
            return True
        except Exception:
            return False

    def show(self, name):
        try:
            result = self.service.get_storage_account_properties(name)
        except Exception as e:
            raise AzureStorageAccountShowError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        return self.__decorate(
            self.__add_containers_to(self.__add_keys_to(result))
        )

    def list(self):
        try:
            results = self.service.list_storage_accounts()
        except Exception as e:
            raise AzureStorageAccountListError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        return [self.__decorate(result) for result in results]

    def __add_keys_to(self, result):
        try:
            keyed_result = self.service.get_storage_account_keys(
                result.service_name
            )
        except Exception as e:
            raise AzureStorageAccountShowError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        result.storage_service_keys = keyed_result.storage_service_keys
        return result

    def __add_containers_to(self, result):
        container_args = {
            'account_name': result.service_name,
            'key': result.storage_service_keys.primary,
            'blob_service_host_base': self.account.get_blob_service_host_base()
        }
        result.containers = Container(**container_args).list()
        return result

    def __decorate(self, result):
        decorated = {
            'name': result.service_name,
            'description': result.storage_service_properties.description,
            'label': result.storage_service_properties.label,
            'backup-strategy': Defaults.docopt_for_account_type(
                result.storage_service_properties.account_type
            ),
            'region': result.storage_service_properties.geo_primary_region,
            'status': result.storage_service_properties.status,
            'backup': {
                'status': result.storage_service_properties.status_of_primary,
            },
            'endpoints': result.storage_service_properties.endpoints
        }
        if decorated['backup-strategy'] != '--locally-redundant':
            decorated['backup'].update({
                'backup-region': result.storage_service_properties.geo_secondary_region,
                'backup-region-status': result.storage_service_properties.status_of_secondary,
                'last-failover': result.storage_service_properties.last_geo_failover_time
            })
        if hasattr(result, 'containers') and result.containers:
            decorated['containers'] = result.containers
        if result.storage_service_keys:
            decorated['keys'] = {
                'primary': result.storage_service_keys.primary,
                'secondary': result.storage_service_keys.secondary
            }
        return decorated
