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

import os
import logging
import sys
from os.path import join as pjoin

import libcloud
import libcloud.security
from cliff.app import App

from raxcli.command_manager import AppCommandManager
from raxcli.actions import HelpAction
from raxcli import __version__

CA_CERT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            'data/cacert.pem')
APPS_PATH = pjoin(os.path.abspath(os.path.dirname(__file__)), 'apps/')
libcloud.security.CA_CERTS_PATH.insert(0, CA_CERT_PATH)


class RaxCliApp(App):

    log = logging.getLogger(__name__)

    DEFAULT_VERBOSE_LEVEL = 0

    def __init__(self):
        super(RaxCliApp, self).__init__(
            description='Rackspace Cloud Command Line Client',
            version=__version__,
            command_manager=AppCommandManager('raxcli', APPS_PATH),
        )

    def build_option_parser(self, description, version):
        argparse_kwargs = {'conflict_handler': 'resolve'}
        parser = super(RaxCliApp, self).\
            build_option_parser(description,
                                version,
                                argparse_kwargs=argparse_kwargs)
        parser.add_argument(
            '-h', '--help',
            action=HelpAction,
            nargs=0,
            default=self,
            help='show this help message and exit',
        )
        return parser


def main(argv=sys.argv[1:]):
    if '--debug' in argv:
        # TODO: improve --debug support, done here very early so we can
        # see everything possible.
        file_path = '/dev/stderr'
        file_handle = open(file_path, 'a')
        libcloud.enable_debug(file_handle)
        logging.basicConfig(filename=file_path,
                            filemode='w',
                            level=logging.DEBUG)
    myapp = RaxCliApp()
    return myapp.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
