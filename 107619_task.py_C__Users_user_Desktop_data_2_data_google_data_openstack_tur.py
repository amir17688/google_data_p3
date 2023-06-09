# Copyright 2013 Rackspace Australia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import logging

from turbo_hipster.lib import models


class Runner(models.ShellTask):

    """A plugin to run any shell script as defined in the config. Based on
    models.ShellTask the steps can be overwritten."""

    log = logging.getLogger("task_plugins.shell_script.task.Runner")
