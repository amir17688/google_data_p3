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
import sys
import glob


class ConfigFilePath(object):
    """
        File path management for config files
    """
    PLATFORM = sys.platform[:3]

    def __init__(self, account_name=None, platform=PLATFORM):
        self.platform = platform
        self.config_directories_in_home = [
            '.config/azurectl/', '.azurectl/'
        ]
        self.config_files = []
        self.account_config_file = None
        for directory in self.config_directories_in_home:
            self.config_files.append(directory + 'config')

        if account_name:
            self.account_config_file = \
                self.config_directories_in_home[0] + account_name + '.config'

        self.home_path = self.__home_path()

    def default_new_config(self):
        """
            The fully qualified path of the preferred config,
            for use when creating a new config
        """
        return self.__full_qualified_config(self.config_files[0])

    def default_new_account_config(self):
        """
            The fully qualified path of the config file when
            using an account name
        """
        return self.__full_qualified_config(self.account_config_file)

    def default_config(self):
        """
            Find and return the path of the first config file that exists
        """
        for filename in self.config_files:
            full_qualified_config = self.__full_qualified_config(filename)
            if os.path.isfile(full_qualified_config):
                return full_qualified_config

    def account_config(self):
        """
            Find and return the path to the account config files that exists
        """
        glob_match = '/'.join(
            [
                self.__home_path(),
                self.config_directories_in_home[0] + '*.config'
            ]
        )
        return list(glob.iglob(glob_match))

    def __home_path(self):
        homeEnvVar = 'HOME'
        if self.platform == 'win':
            if 'HOMEPATH' in os.environ:
                homeEnvVar = 'HOMEPATH'
            else:
                homeEnvVar = 'UserProfile'
        return os.environ[homeEnvVar]

    def __full_qualified_config(self, filename):
        return self.__home_path() + '/' + filename
