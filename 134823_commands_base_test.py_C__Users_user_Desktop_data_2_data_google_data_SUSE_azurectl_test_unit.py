import sys
import mock

from mock import patch

import logging

from test_helper import *

import azurectl

from azurectl.commands.base import CliTask
from azurectl.azurectl_exceptions import *


class TestCliTask:
    @raises(SystemExit)
    @patch('azurectl.commands.base.Help.show')
    def test_show_help(self, help_show):
        sys.argv = [
            sys.argv[0], 'help'
        ]
        CliTask()
        help_show.assert_called_once_with('azurectl')

    @patch('azurectl.commands.base.Cli.show_help')
    @patch('azurectl.logger.log.setLevel')
    def test_cli_init(self, mock_loglevel, mock_show_help):
        sys.argv = [
            sys.argv[0],
            '--debug',
            '--region', 'region',
            '--config', 'config',
            'storage', 'container', 'list'
        ]
        mock_show_help.return_value = False
        task = CliTask()
        mock_loglevel.assert_called_once_with(logging.DEBUG)

    @patch('azurectl.commands.base.Validations.validate_min_length')
    def test_validate_min_length(self, mock_validation):
        sys.argv = [
            sys.argv[0],
            'setup', 'account', 'region', 'default', '--name', 'test-name0',
            '--region', 'some-region'
        ]
        task = CliTask()
        task.validate_min_length('--name', 5)
        mock_validation.assert_called_once_with('--name', 'test-name0', 5)

    @patch('azurectl.commands.base.Validations.validate_max_length')
    def test_validate_max_length(self, mock_validation):
        sys.argv = [
            sys.argv[0],
            'setup', 'account', 'region', 'default', '--name', 'test-name0',
            '--region', 'some-region'
        ]
        task = CliTask()
        task.validate_max_length('--name', 10)
        mock_validation.assert_called_once_with('--name', 'test-name0', 10)

    @patch('azurectl.commands.base.Cli.show_help')
    @patch('azurectl.commands.base.Config')
    @patch('azurectl.logger.log.setLevel')
    def test_load_config(
        self, mock_loglevel, mock_config, mock_show_help
    ):
        sys.argv = [
            sys.argv[0],
            '--debug',
            '--region', 'region',
            '--config', 'config',
            'storage', 'container', 'list'
        ]
        mock_show_help.return_value = False
        task = CliTask()
        task.load_config()
        mock_config.assert_called_once_with(
            None, 'region', None, None, 'config'
        )
        mock_loglevel.assert_called_once_with(logging.DEBUG)
