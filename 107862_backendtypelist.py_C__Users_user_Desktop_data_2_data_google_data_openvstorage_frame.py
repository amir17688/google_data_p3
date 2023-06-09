# Copyright 2016 iNuron NV
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
BackendTypeList module
"""
from ovs.dal.datalist import DataList
from ovs.dal.hybrids.backendtype import BackendType


class BackendTypeList(object):
    """
    This BackendTypeList class contains various lists regarding to the BackendType class
    """

    @staticmethod
    def get_backend_types():
        """
        Returns a list of all Backends
        """
        return DataList(BackendType, {'type': DataList.where_operator.AND,
                                      'items': []})

    @staticmethod
    def get_backend_type_by_code(code):
        """
        Returns a single BackendType for the given code. Returns None if no BackendType was found
        """
        backendtypes = DataList(BackendType, {'type': DataList.where_operator.AND,
                                              'items': [('code', DataList.operator.EQUALS, code)]})
        if len(backendtypes) == 1:
            return backendtypes[0]
        return None
