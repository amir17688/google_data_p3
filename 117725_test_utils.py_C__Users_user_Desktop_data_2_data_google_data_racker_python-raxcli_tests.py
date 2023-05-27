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

import sys
import unittest2 as unittest

from raxcli.utils import get_enum_as_dict


class TestUtils(unittest.TestCase):
    def test_get_enum_as_dict(self):
        class EnumClass1(object):
            KEY1 = 0
            KEY_TWO_TWO = 1
            SOME_KEY_SOME_SOME = 2

        result1 = get_enum_as_dict(EnumClass1, friendly_names=False)
        result2 = get_enum_as_dict(EnumClass1, friendly_names=True)
        result1_reversed = get_enum_as_dict(EnumClass1, reverse=True,
                                            friendly_names=False)

        expected1 = {
            'KEY1': 0,
            'KEY_TWO_TWO': 1,
            'SOME_KEY_SOME_SOME': 2
        }

        expected2 = {
            'Key1': 0,
            'Key Two Two': 1,
            'Some Key Some Some': 2
        }

        expected3 = {
            0: 'KEY1',
            1: 'KEY_TWO_TWO',
            2: 'SOME_KEY_SOME_SOME'
        }
        self.assertDictEqual(result1, expected1)
        self.assertDictEqual(result2, expected2)
        self.assertDictEqual(result1_reversed, expected3)


if __name__ == '__main__':
    sys.exit(unittest.main())
