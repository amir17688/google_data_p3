import sys
import mock
from mock import patch
from mock import call


from test_helper import *

from azurectl.azurectl_exceptions import *
from azurectl.storage.storage import Storage

import azurectl

from collections import namedtuple


class TestStorage:
    def setup(self):
        account = mock.Mock()
        credentials = namedtuple(
            'credentials',
            ['private_key', 'certificate', 'subscription_id']
        )
        account.publishsettings = mock.Mock(
            return_value=credentials(
                private_key='abc',
                certificate='abc',
                subscription_id='4711'
            )
        )
        self.storage = Storage(account, 'some-container')

    @raises(AzureStorageFileNotFound)
    @patch('os.path.exists')
    def test_upload_storage_file_not_found(self, mock_exists):
        mock_exists.return_value = False
        self.storage.upload('some-blob', None)

    @raises(AzureStorageStreamError)
    @patch('azurectl.storage.storage.XZ.open')
    def test_upload_error_put_blob(self, mock_xz_open):
        mock_xz_open.side_effect = Exception
        self.storage.upload('../data/blob.xz')

    @raises(AzureStorageUploadError)
    @patch('azurectl.storage.storage.PageBlob')
    @patch('azurectl.storage.storage.XZ.open')
    def test_upload_raises(self, mock_xz_open, mock_page_blob):
        stream = mock.Mock
        stream.close = mock.Mock()
        mock_xz_open.return_value = stream
        mock_page_blob.side_effect = Exception
        self.storage.upload('../data/blob.xz')
        stream.close.assert_called_once_with()

    @patch('azurectl.storage.storage.PageBlob')
    @patch('azurectl.storage.storage.XZ.uncompressed_size')
    @patch('azurectl.storage.storage.XZ.open')
    def test_upload(self, mock_xz_open, mock_uncompressed_size, mock_page_blob):
        stream = mock.Mock
        stream.close = mock.Mock()
        mock_xz_open.return_value = stream
        page_blob = mock.Mock()
        next_results = [3, 2, 1]

        def side_effect(stream, max_chunk_size, max_attempts):
            try:
                return next_results.pop()
            except:
                raise StopIteration

        page_blob.next.side_effect = side_effect
        mock_page_blob.return_value = page_blob
        mock_uncompressed_size.return_value = 1024

        self.storage.upload('../data/blob.xz')

        assert page_blob.next.call_args_list == [
            call(stream, None, 5),
            call(stream, None, 5),
            call(stream, None, 5),
            call(stream, None, 5)
        ]
        stream.close.assert_called_once_with()

    @patch('azurectl.storage.storage.PageBlob')
    @patch('__builtin__.open')
    @patch('os.path.getsize')
    def test_upload_uncompressed(
        self, mock_uncompressed_size, mock_open, mock_page_blob
    ):
        stream = mock.Mock
        stream.close = mock.Mock()
        mock_open.return_value = stream
        page_blob = mock.Mock()
        next_results = [3, 2, 1]

        def side_effect(stream, max_chunk_size, max_attempts):
            try:
                return next_results.pop()
            except:
                raise StopIteration

        page_blob.next.side_effect = side_effect
        mock_page_blob.return_value = page_blob
        mock_uncompressed_size.return_value = 1024

        self.storage.upload('../data/blob.raw')

        assert page_blob.next.call_args_list == [
            call(stream, None, 5),
            call(stream, None, 5),
            call(stream, None, 5),
            call(stream, None, 5)
        ]
        stream.close.assert_called_once_with()

    @raises(AzureStorageDeleteError)
    def test_delete(self):
        self.storage.delete('some-blob')

    def test_print_upload_status(self):
        self.storage.print_upload_status()
        assert self.storage.upload_status == \
            {'current_bytes': 0, 'total_bytes': 0}
