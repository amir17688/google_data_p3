"""
Tests for `workbench` module.
"""

import zerorpc
import pytest
import workbench_singleton # This spins up the server

#pylint: disable=no-member
@pytest.fixture(scope='session')
#pylint: enable=no-member
def workbench_conn(request):
    ''' Workbench Fixture '''

    # Connect to the server
    conn = zerorpc.Client(timeout=300, heartbeat=60)
    conn.connect('tcp://localhost:4242')

    # Add a finalize method
    request.addfinalizer(workbench_singleton.shutdown)

    # Return the connection
    return conn
