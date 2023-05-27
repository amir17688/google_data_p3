import dateutil.parser
import sys
import mock
from mock import patch


from test_helper import *

from azurectl.commands.storage_disk import StorageDiskTask


class TestStorageDiskTask:
    def setup(self):
        sys.argv = [
            sys.argv[0], '--config', '../data/config',
            'storage', 'disk', 'upload',
            '--source', 'blob',
            '--blob-name', 'name'
        ]
        azurectl.commands.storage_disk.AzureAccount.storage_names = mock.Mock(
            return_value=mock.Mock()
        )
        self.storage = mock.Mock()
        self.storage.upload = mock.Mock()
        azurectl.commands.storage_disk.Storage = mock.Mock(
            return_value=self.storage
        )
        azurectl.commands.storage_disk.Help = mock.Mock(
            return_value=mock.Mock()
        )
        self.task = StorageDiskTask()
        self.__init_command_args()

    def __init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['disk'] = False
        self.task.command_args['delete'] = False
        self.task.command_args['upload'] = False
        self.task.command_args['--color'] = False
        self.task.command_args['--source'] = 'some-file'
        self.task.command_args['--max-chunk-size'] = 1024
        self.task.command_args['--quiet'] = False
        self.task.command_args['--blob-name'] = 'some-name'
        self.task.command_args['help'] = False

    @patch('azurectl.commands.storage_disk.BackgroundScheduler')
    def test_process_storage_disk_upload(self, mock_job):
        self.__init_command_args()
        self.task.command_args['disk'] = True
        self.task.command_args['upload'] = True
        self.task.process()
        self.task.storage.upload.assert_called_once_with(
            'some-file', self.task.command_args['--blob-name'], 1024
        )

    @raises(SystemExit)
    @patch('azurectl.commands.storage_disk.BackgroundScheduler')
    def test_process_storage_disk_upload_interrupted(self, mock_job):
        self.__init_command_args()
        self.task.command_args['disk'] = True
        self.task.command_args['upload'] = True
        self.storage.upload.side_effect = KeyboardInterrupt
        self.task.process()

    @raises(SystemExit)
    @patch('azurectl.commands.storage_disk.BackgroundScheduler')
    def test_process_storage_disk_upload_quiet_interrupted(self, mock_job):
        self.__init_command_args()
        self.task.command_args['disk'] = True
        self.task.command_args['upload'] = True
        self.task.command_args['--quiet'] = True
        self.storage.upload.side_effect = KeyboardInterrupt
        self.task.process()

    def test_process_storage_disk_delete(self):
        self.__init_command_args()
        self.task.command_args['disk'] = True
        self.task.command_args['delete'] = True
        self.task.process()
        self.task.storage.delete.assert_called_once_with(
            self.task.command_args['--blob-name']
        )

    def test_process_storage_disk_help(self):
        self.__init_command_args()
        self.task.command_args['help'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'azurectl::storage::disk'
        )
