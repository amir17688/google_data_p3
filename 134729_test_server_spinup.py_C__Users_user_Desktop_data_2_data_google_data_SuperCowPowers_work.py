''' This spins up a workbench server for the tests to hit '''

class TestServerSpinup(object):
    ''' Spin up a Worbench test server '''

    def test_server_spinup(self, workbench_conn):
        ''' Start the workbench Server: although it looks like this
            test doesn't do anything, because it hits the 'workbench_conn'
            fixture a workbench server will spin up '''

        print '\nStarting up the Workbench server...'
        print workbench_conn
        return True
