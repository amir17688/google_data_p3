
''' view_zip_deep worker '''
import os
import zerorpc
import pprint

class ViewZipDeep(object):
    ''' ViewZipDeep: Generates a view for Zip files '''
    dependencies = ['view_zip']

    def __init__(self):
        self.workbench = zerorpc.Client(timeout=300, heartbeat=60)
        self.workbench.connect("tcp://127.0.0.1:4242")

    def execute(self, input_data):
        ''' Execute the ViewZipDeep worker '''
        view = {}
        view.update(input_data['view_zip'])
        return view

    def __del__(self):
        ''' Class Cleanup '''
        # Close zeroRPC client
        self.workbench.close()

# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' -- view_zip_deep.py test -- '''

    # This worker test requires a local server running
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate input for the worker
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/zip/bad.zip')
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'bad.zip', 'zip')
    input_data = workbench.work_request('view_zip', md5)

    # Execute the worker (unit test)
    worker = ViewZipDeep()
    output = worker.execute(input_data)
    print '\n<<< Unit Test >>>'
    pprint.pprint(output)

    # Execute the worker (server test)
    output = workbench.work_request('view_zip_deep', md5)
    print '\n<<< Server Test >>>'
    pprint.pprint(output)

if __name__ == "__main__":
    test()
