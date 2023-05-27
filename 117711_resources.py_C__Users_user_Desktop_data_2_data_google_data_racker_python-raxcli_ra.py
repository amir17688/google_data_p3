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

from raxcli.models import Attribute, Model


class Check(Model):
    """
    Check resource.
    """
    id = Attribute()
    label = Attribute()
    type = Attribute()
    entity_id = Attribute(view_list=False)
    monitoring_zones = Attribute(view_list=False)
    period = Attribute(view_list=False)
    timeout = Attribute(view_list=False)
    target_alias = Attribute(view_list=False)
    target_resolver = Attribute(view_list=False)
    disabled = Attribute(view_list=False)
    details = Attribute(view_list=False)


class Entity(Model):
    """
    Entity resource.
    """
    id = Attribute()
    label = Attribute()
    uri = Attribute()
    extra = Attribute(view_list=False)
    agent_id = Attribute(view_list=False)
    ip_addresses = Attribute(view_list=False)


class AgentToken(Model):
    """
    Agent token resource.
    """
    id = Attribute()
    label = Attribute()
    token = Attribute()


class Alarm(Model):
    """
    Alarm resource.
    """
    id = Attribute()
    label = Attribute()
    check_id = Attribute()
    criteria = Attribute(view_list=False)
    notification_plan_id = Attribute(view_list=False)
