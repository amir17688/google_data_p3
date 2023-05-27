# Copyright (c) 2016 SUSE.  All rights reserved.
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
# project
from ..azurectl_exceptions import AzureInvalidCommand


class Validations(object):
    @classmethod
    def validate_min_length(self, field_name, value, min_length):
        if len(value) < min_length:
            raise AzureInvalidCommand(
                '%s is too short. Length must be at least %d characters.' %
                (field_name, min_length))
        return True

    @classmethod
    def validate_max_length(self, field_name, value, max_length):
        if len(value) > max_length:
            raise AzureInvalidCommand(
                '%s is too long. Length must be at most %d characters.' %
                (field_name, max_length))
        return True
