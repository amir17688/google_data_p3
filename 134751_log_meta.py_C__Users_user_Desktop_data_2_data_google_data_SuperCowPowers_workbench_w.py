
''' Logfile Meta worker '''
import pprint

class LogMetaData(object):
    ''' This worker computes a meta-data for log files. '''
    dependencies = ['sample', 'meta']

    def __init__(self):
        ''' Initialization '''
        self.meta = {}

    def execute(self, input_data):
        raw_bytes = input_data['sample']['raw_bytes']
        self.meta['num_rows'] = raw_bytes.count('\n')
        self.meta['head'] = raw_bytes[:100]
        self.meta['tail'] = raw_bytes[-100:]
        self.meta.update(input_data['meta'])
        return self.meta


# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' log_meta.py: Unit test'''

    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate input for the worker
    import os
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/log/system.log')
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'system.log', 'log')
    input_data = workbench.get_sample(md5)
    input_data.update(workbench.work_request('meta', md5))

    # Execute the worker (unit test)
    worker = LogMetaData()
    output = worker.execute(input_data)
    print '\n<<< Unit Test >>>'
    pprint.pprint(output)

    # Execute the worker (server test)
    output = workbench.work_request('log_meta', md5)
    print '\n<<< Server Test >>>'
    pprint.pprint(output)

if __name__ == "__main__":
    test()
