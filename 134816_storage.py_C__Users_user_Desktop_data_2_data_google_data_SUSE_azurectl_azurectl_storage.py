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
import os
from azure.storage.blob.pageblobservice import PageBlobService

# project
from ..utils.xz import XZ
from ..azurectl_exceptions import (
    AzureStorageFileNotFound,
    AzureStorageStreamError,
    AzureStorageUploadError,
    AzureStorageDeleteError
)
from ..utils.filetype import FileType
from .page_blob import PageBlob
from ..logger import log


class Storage(object):
    """
        Implements storage operations in Azure storage containers
    """
    def __init__(self, account, container):
        self.account = account
        self.account_name = account.storage_name()
        self.account_key = account.storage_key()
        self.blob_service_host_base = self.account.get_blob_service_host_base()
        self.container = container
        self.upload_status = {'current_bytes': 0, 'total_bytes': 0}

    def upload(self, image, name=None, max_chunk_size=None, max_attempts=5):
        if not os.path.exists(image):
            raise AzureStorageFileNotFound('File %s not found' % image)
        blob_service = PageBlobService(
            self.account_name,
            self.account_key,
            endpoint_suffix=self.blob_service_host_base
        )

        image_type = FileType(image)
        blob_name = (name or image_type.basename())
        if not name:
            log.info('blob-name: %s', blob_name)
        image_size = self.__upload_byte_size(image, image_type)

        try:
            stream = self.__open_upload_stream(image, image_type)
        except Exception as e:
            raise AzureStorageStreamError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        try:
            page_blob = PageBlob(
                blob_service, blob_name, self.container, image_size
            )
            self.__upload_status(0, image_size)
            while True:
                bytes_transfered = page_blob.next(
                    stream, max_chunk_size, max_attempts
                )
                self.__upload_status(bytes_transfered, image_size)
        except StopIteration:
            stream.close()
            self.__upload_status(image_size, image_size)
        except Exception as e:
            stream.close()
            raise AzureStorageUploadError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def delete(self, image):
        blob_service = PageBlobService(
            self.account_name,
            self.account_key,
            endpoint_suffix=self.blob_service_host_base
        )
        try:
            blob_service.delete_blob(self.container, image)
        except Exception as e:
            raise AzureStorageDeleteError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def print_upload_status(self):
        log.progress(
            self.upload_status['current_bytes'],
            self.upload_status['total_bytes'],
            'Uploading'
        )

    def __upload_status(self, current, total):
        self.upload_status['current_bytes'] = current
        self.upload_status['total_bytes'] = total

    def __open_upload_stream(self, image, image_type):
        if image_type.is_xz():
            return XZ.open(image)
        return open(image)

    def __upload_byte_size(self, image, image_type):
        if image_type.is_xz():
            return XZ.uncompressed_size(image)
        return os.path.getsize(image)
