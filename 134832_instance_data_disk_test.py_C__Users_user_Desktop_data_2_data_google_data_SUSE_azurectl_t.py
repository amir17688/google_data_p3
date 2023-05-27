import sys
import mock
import random
from azure.common import AzureMissingResourceHttpError
from collections import namedtuple
from datetime import datetime
from mock import patch
from test_helper import *

from azurectl.account.service import AzureAccount
from azurectl.azurectl_exceptions import *
from azurectl.config.parser import Config
from azurectl.instance.data_disk import DataDisk

import azurectl


class TestDataDisk:
    def setup(self):
        # construct an account
        account = AzureAccount(
            Config(
                region_name='East US 2', filename='../data/config'
            )
        )
        self.service = mock.Mock()
        account.get_management_service = mock.Mock(return_value=self.service)
        account.get_blob_service_host_base = mock.Mock(
            return_value='test.url'
        )
        account.storage_key = mock.Mock()
        # now that that's done, instantiate a DataDisk with the account
        self.data_disk = DataDisk(account)
        # asynchronous API operations return a request object
        self.my_request = mock.Mock(request_id=42)
        # variables used in multiple tests
        self.cloud_service_name = 'mockcloudservice'
        self.instance_name = 'mockcloudserviceinstance1'
        self.lun = 0
        self.host_caching = 'ReadWrite'
        self.disk_filename = 'mockcloudserviceinstance1-data-disk-0.vhd'
        self.disk_url = (
            'https://' +
            account.storage_name() +
            '.blob.' +
            account.get_blob_service_host_base() + '/' +
            account.storage_container() + '/' +
            self.disk_filename
        )
        self.disk_label = 'Mock data disk'
        self.disk_size = 42
        self.timestamp = datetime.utcnow()
        self.time_string = datetime.isoformat(self.timestamp)

    def create_mock_data_disk(self, lun):
        return mock.Mock(
            host_caching=self.host_caching,
            disk_label=self.disk_label,
            disk_name='',
            lun=lun,
            logical_disk_size_in_gb=self.disk_size,
            media_link=self.disk_url,
            source_media_link=''
        )

    def create_expected_data_disk_output(self, lun):
        return {
            'size': '%d GB' % self.disk_size,
            'label': self.disk_label,
            'disk-url': self.disk_url,
            'source-image-url': '',
            'lun': lun,
            'host-caching': 'ReadWrite'
        }

    def test_create(self):
        # given
        self.service.add_data_disk.return_value = self.my_request
        # when
        result = self.data_disk.create(
            self.cloud_service_name,
            self.instance_name,
            self.disk_size,
            lun=self.lun,
            host_caching=self.host_caching,
            filename=self.disk_filename,
            label=self.disk_label
        )
        # then
        assert result == self.my_request.request_id
        self.service.add_data_disk.assert_called_once_with(
            self.cloud_service_name,
            self.instance_name,
            self.cloud_service_name,
            self.lun,
            host_caching=self.host_caching,
            media_link=self.disk_url,
            disk_label=self.disk_label,
            logical_disk_size_in_gb=self.disk_size
        )

    @raises(AzureDataDiskCreateError)
    def test_create_upstream_exception(self):
        # given
        self.service.add_data_disk.side_effect = Exception
        # when
        self.data_disk.create(
            self.cloud_service_name,
            self.instance_name,
            self.disk_size,
            lun=self.lun,
            host_caching=self.host_caching,
            filename=self.disk_filename,
            label=self.disk_label
        )

    def test_get_first_available_lun(self):
        # given
        self.service.get_data_disk.side_effect = iter([
            self.create_mock_data_disk(0),
            self.create_mock_data_disk(1),
            AzureMissingResourceHttpError('NOT FOUND', 404)
        ])
        # when
        result = self.data_disk._DataDisk__get_first_available_lun(
            self.cloud_service_name,
            self.instance_name
        )
        # then
        assert self.service.get_data_disk.call_count == 3
        assert result == 2  # 0 and 1 are taken

    @raises(AzureDataDiskNoAvailableLun)
    def test_no_available_lun_exception(self):
        # given
        self.service.get_data_disk.side_effect = iter([
            self.create_mock_data_disk(i) for i in range(16)
        ])
        # when
        self.data_disk._DataDisk__get_first_available_lun(
            self.cloud_service_name,
            self.instance_name
        )
        # then
        assert self.service.get_data_disk.call_count == 16

    @patch('azurectl.instance.data_disk.DataDisk._DataDisk__get_first_available_lun')
    def test_create_without_lun(self, mock_lun):
        # given
        self.service.add_data_disk.return_value = self.my_request
        mock_lun.return_value = 0
        # when
        result = self.data_disk.create(
            self.cloud_service_name,
            self.instance_name,
            self.disk_size,
            # lun=self.lun,
            host_caching=self.host_caching,
            filename=self.disk_filename,
            label=self.disk_label
        )
        # then
        self.service.add_data_disk.assert_called_once_with(
            self.cloud_service_name,
            self.instance_name,
            self.cloud_service_name,
            0,
            host_caching=self.host_caching,
            media_link=self.disk_url,
            disk_label=self.disk_label,
            logical_disk_size_in_gb=self.disk_size
        )

    @patch('azurectl.instance.data_disk.datetime')
    def test_generate_filename(self, mock_timestamp):
        # given
        mock_timestamp.utcnow = mock.Mock(return_value=self.timestamp)
        mock_timestamp.isoformat = mock.Mock(return_value=self.time_string)
        expected = '%s-data-disk-%s.vhd' % (
            self.instance_name,
            self.time_string
        )
        # when
        result = self.data_disk._DataDisk__generate_filename(self.instance_name)
        # then
        assert result == expected

    @patch('azurectl.instance.data_disk.DataDisk._DataDisk__generate_filename')
    def test_create_without_filename(self, mock_generate_filename):
        # given
        self.service.add_data_disk.return_value = self.my_request
        mock_generate_filename.return_value = self.disk_filename
        # when
        result = self.data_disk.create(
            self.cloud_service_name,
            self.instance_name,
            self.disk_size,
            lun=self.lun,
            host_caching=self.host_caching,
            # filename=self.disk_filename,
            label=self.disk_label
        )
        # then
        self.service.add_data_disk.assert_called_once_with(
            self.cloud_service_name,
            self.instance_name,
            self.cloud_service_name,
            self.lun,
            host_caching=self.host_caching,
            media_link=self.disk_url,
            disk_label=self.disk_label,
            logical_disk_size_in_gb=self.disk_size
        )

    def test_show(self):
        # given
        self.service.get_data_disk.return_value = self.create_mock_data_disk(
            self.lun
        )
        expected = self.create_expected_data_disk_output(self.lun)
        # when
        result = self.data_disk.show(
            self.cloud_service_name,
            self.instance_name,
            self.lun
        )
        # then
        self.service.get_data_disk.assert_called_once_with(
            self.cloud_service_name,
            self.instance_name,
            self.cloud_service_name,
            self.lun
        )
        assert result == expected

    @raises(AzureDataDiskShowError)
    def test_show_upsteam_exception(self):
        # given
        self.service.get_data_disk.side_effect = Exception
        # when
        self.data_disk.show(
            self.cloud_service_name,
            self.instance_name,
            self.lun
        )

    def test_delete(self):
        # given
        self.service.delete_data_disk.return_value = self.my_request
        # when
        result = self.data_disk.delete(
            self.cloud_service_name,
            self.instance_name,
            self.lun
        )
        # then
        self.service.delete_data_disk.assert_called_once_with(
            self.cloud_service_name,
            self.instance_name,
            self.cloud_service_name,
            self.lun,
            delete_vhd=True
        )
        assert result == self.my_request.request_id

    @raises(AzureDataDiskDeleteError)
    def test_delete_with_upstream_exception(self):
        # given
        self.service.delete_data_disk.side_effect = Exception
        # when
        self.data_disk.delete(
            self.cloud_service_name,
            self.instance_name,
            self.lun
        )

    def test_list(self):
        # given
        number_of_disks = random.randint(0, 15)
        luns = random.sample(range(16), number_of_disks)
        luns.sort()
        mock_disk_set = [AzureMissingResourceHttpError('NOT FOUND', 404)] * 16
        expected_result = []
        for lun in luns:
            mock_disk_set[lun] = self.create_mock_data_disk(lun)
            expected_result.append(self.create_expected_data_disk_output(lun))
        self.service.get_data_disk.side_effect = iter(mock_disk_set)
        # when
        result = self.data_disk.list(
            self.cloud_service_name,
            self.instance_name
        )
        # then
        assert result == expected_result
