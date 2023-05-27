
''' view_zip worker '''
import os
import zerorpc
import pprint

class ViewZip(object):
    ''' ViewZip: Generates a view for Zip files '''
    dependencies = ['meta', 'unzip', 'yara_sigs']

    def __init__(self):
        self.workbench = zerorpc.Client(timeout=300, heartbeat=60)
        self.workbench.connect("tcp://127.0.0.1:4242")

    def execute(self, input_data):
        ''' Execute the ViewZip worker '''

        # Just a small check to make sure we haven't been called on the wrong file type
        if (input_data['meta']['type_tag'] != 'zip'):
            return {'error': self.__class__.__name__+': called on '+input_data['meta']['type_tag']}

        view = {}
        view['payload_md5s'] = input_data['unzip']['payload_md5s']
        view['yara_sigs'] = input_data['yara_sigs']['matches'].keys()
        view.update(input_data['meta'])

        # Okay this view is going to also give the meta data about the payloads
        view['payload_meta'] = [self.workbench.work_request('meta', md5) for md5 in input_data['unzip']['payload_md5s']]
        return view

    def __del__(self):
        ''' Class Cleanup '''
        # Close zeroRPC client
        self.workbench.close()

# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' -- view_zip.py test -- '''

    # This worker test requires a local server running
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate input for the worker
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/zip/bad.zip')
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'bad.zip', 'zip')
    input_data = workbench.work_request('meta', md5)
    input_data.update(workbench.work_request('unzip', md5))
    input_data.update(workbench.work_request('yara_sigs', md5))

    # Execute the worker (unit test)
    worker = ViewZip()
    output = worker.execute(input_data)
    print '\n<<< Unit Test >>>'
    pprint.pprint(output)

    # Execute the worker (server test)
    output = workbench.work_request('view_zip', md5)
    print '\n<<< Server Test >>>'
    pprint.pprint(output)

if __name__ == "__main__":
    test()
