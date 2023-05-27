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
import sys
import unittest2 as unittest

from os.path import join as pjoin

from raxcli.config import get_config, DEFAULT_ENV_PREFIX

FIXTURES_DIR = pjoin(os.path.dirname(os.path.abspath(__file__)), 'fixtures/')


class TestConfigParsing(unittest.TestCase):
    def test_config_from_file_global_section_1(self):
        path1 = os.path.join(FIXTURES_DIR, 'config1.ini')
        config = get_config(app=None, config_path=path1)

        self.assertEqual(config['username'], 'username1')
        self.assertEqual(config['api_key'], 'api_key1')
        self.assertEqual(config['verify_ssl'], True)
        self.assertEqual(config['auth_url'], 'http://www.foo.com/1')

    def test_config_from_file_global_section_2(self):
        path1 = os.path.join(FIXTURES_DIR, 'config2.ini')
        config = get_config(app=None, config_path=path1)

        self.assertEqual(config['username'], 'username2')
        self.assertEqual(config['api_key'], 'api_key2')
        self.assertEqual(config['verify_ssl'], False)
        self.assertEqual(config['auth_url'], 'http://www.foo.com/2')

    def test_from_file_global_with_app_section_precedence(self):
        path1 = os.path.join(FIXTURES_DIR, 'config3.ini')
        config = get_config(app='registry', config_path=path1)

        self.assertEqual(config['username'], 'username_registry')
        self.assertEqual(config['api_key'], 'api_key_registry')
        self.assertEqual(config['verify_ssl'], True)
        self.assertEqual(config['auth_url'], 'http://www.foo.com/2')

    def test_config_from_file_only_app_section(self):
        path1 = os.path.join(FIXTURES_DIR, 'config4.ini')

        config = get_config(app='monitoring', config_path=path1)

        self.assertEqual(config['username'], 'username_mon')
        self.assertEqual(config['api_key'], 'api_key_mon')
        self.assertEqual(config['verify_ssl'], True)

    def test_config_from_file_default_values(self):
        path1 = os.path.join(FIXTURES_DIR, 'config5.ini')

        default_values = {'username': 'username_def', 'api_key': 'api_key_def',
                          'verify_ssl': True, 'auth_url': 'aurl_def'}
        config = get_config(app='monitoring', config_path=path1,
                            default_values=default_values)

        self.assertEqual(config['username'], 'username_def')
        self.assertEqual(config['api_key'], 'api_key_def')
        self.assertEqual(config['verify_ssl'], True)
        self.assertEqual(config['auth_url'], 'aurl_def')

    def test_config_from_file_default_values_and_env(self):
        path1 = os.path.join(FIXTURES_DIR, 'config5.ini')

        default_values = {'username': 'username_def', 'api_key': 'api_key_def',
                          'verify_ssl': True, 'auth_url': 'aurl_def'}
        env_dict = {}
        env_dict[DEFAULT_ENV_PREFIX + 'USERNAME'] = 'username_env'
        env_dict[DEFAULT_ENV_PREFIX + 'VERIFY_SSL'] = 'false'

        config = get_config(app='monitoring', config_path=path1,
                            default_values=default_values, env_dict=env_dict)

        self.assertEqual(config['username'], 'username_env')
        self.assertEqual(config['api_key'], 'api_key_def')
        self.assertEqual(config['verify_ssl'], False)
        self.assertEqual(config['auth_url'], 'aurl_def')


if __name__ == '__main__':
    sys.exit(unittest.main())
