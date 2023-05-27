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
import sys
import logging

# project
from ..cli import Cli
from ..config.parser import Config
from ..help import Help
from ..utils.validations import Validations


class CliTask(object):
    """
        Base class for all task classes, loads the task and provides
        the interface to the command options and the account to use
        for the task
    """
    def __init__(self):
        from ..logger import log

        self.cli = Cli()

        # show main help man page if requested
        if self.cli.show_help():
            manual = Help()
            manual.show('azurectl')
            sys.exit(0)

        # load/import task module
        self.task = self.cli.load_command()

        # get command specific args
        self.command_args = self.cli.get_command_args()

        # get global args
        self.global_args = self.cli.get_global_args()

        # set log level
        if self.global_args['--debug']:
            log.setLevel(logging.DEBUG)

    def load_config(self):
        self.config = Config(
            self.global_args['--account'],
            self.global_args['--region'],
            self.global_args['--storage-account'],
            self.global_args['--storage-container'],
            self.global_args['--config']
        )
        self.config_file = self.config.config_file

    def validate_min_length(self, cmd_arg, min_length):
        Validations.validate_min_length(
            cmd_arg,
            self.command_args[cmd_arg],
            min_length
        )

    def validate_max_length(self, cmd_arg, max_length):
        Validations.validate_max_length(
            cmd_arg,
            self.command_args[cmd_arg],
            max_length
        )
