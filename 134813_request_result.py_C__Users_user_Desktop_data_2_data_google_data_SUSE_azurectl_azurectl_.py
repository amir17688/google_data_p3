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
import time

# project
from ..azurectl_exceptions import (
    AzureRequestStatusError,
    AzureRequestTimeout,
    AzureRequestError
)


class RequestResult(object):
    """
        operate on azure request ID and provide methods
        to get status information as well as define operations
        based on the request status
    """
    def __init__(self, request_id):
        self.request_id = request_id

        # set request status wait timeout to 300s (5min)
        self.request_timeout_count = 60
        self.request_timeout = 5

    def status(self, service):
        """
            query status for given request id
        """
        try:
            return service.get_operation_status(self.request_id)
        except Exception as e:
            raise AzureRequestStatusError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def wait_for_request_completion(self, service):
        """
            poll on status, waiting for success until timeout
        """
        count = 0
        result = self.status(service)
        while result.status == 'InProgress':
            count = count + 1
            if count > self.request_timeout_count:
                raise AzureRequestTimeout(
                    'Operation %s timed out' % self.request_id
                )
            time.sleep(self.request_timeout)
            result = self.status(service)

        if result.status != 'Succeeded':
            raise AzureRequestError(
                'Operation %s failed. %s (%s)' % (
                    self.request_id,
                    format(result.error.message),
                    format(result.error.code)
                )
            )
