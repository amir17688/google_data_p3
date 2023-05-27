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
"""
Most requests to the Azure API are asynchronous and return only a request ID.

usage: azurectl compute request -h | --help
       azurectl compute request status --id=<number>
       azurectl compute request wait --id=<number>
       azurectl compute request help

commands:
    help
        show manual page for request command
    status
        print status for given request id
    wait
        wait for request to complete

options:
    --id=<number>
        request id number returned from azurectl for asynchronous request
"""
# project
from base import CliTask
from ..account.service import AzureAccount
from ..utils.collector import DataCollector
from ..utils.output import DataOutput
from ..management.request_result import RequestResult
from ..help import Help


class ComputeRequestTask(CliTask):
    """
        Process request status
    """
    def process(self):
        self.manual = Help()
        if self.__help():
            return

        self.result = DataCollector()
        self.out = DataOutput(
            self.result,
            self.global_args['--output-format'],
            self.global_args['--output-style']
        )

        self.load_config()

        self.account = AzureAccount(self.config)
        self.service = self.account.get_management_service()

        self.request_result = RequestResult(
            self.command_args['--id']
        )
        if self.command_args['status']:
            self.result.add(
                'request:' + format(self.command_args['--id']),
                format(self.__get_status())
            )
            self.out.display()
        elif self.command_args['wait']:
            self.__wait_for_request_to_complete()

    def __get_status(self):
        return self.request_result.status(
            self.service
        )

    def __wait_for_request_to_complete(self):
        self.request_result.wait_for_request_completion(
            self.service
        )

    def __help(self):
        if self.command_args['help']:
            self.manual.show('azurectl::compute::request')
        else:
            return False
        return self.manual
