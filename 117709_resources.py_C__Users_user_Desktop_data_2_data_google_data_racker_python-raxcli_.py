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

__all__ = [
    'Balancer',
    'Member',
    'Algorithm'
]

from libcloud.loadbalancer.types import State

from raxcli.utils import get_enum_as_dict
from raxcli.models import Attribute, Model

STATES = get_enum_as_dict(State, reverse=True)


def state_to_string(value):
    return STATES[value]


class Balancer(Model):
    id = Attribute()
    name = Attribute()
    state = Attribute(transform_func=state_to_string)
    ip = Attribute()
    port = Attribute()


class Member(Model):
    id = Attribute()
    ip = Attribute()
    port = Attribute()


class Algorithm(Model):
    id = Attribute()
    algorithm = Attribute()

    def __cmp__(self, other):
        return cmp(self.id.value, other.id.value)
