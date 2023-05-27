
''' view_pe_deep worker '''
import pprint

class ViewPEDeep(object):
    ''' Generates a high level summary view for PE files that incorporates a large set of workers '''
    dependencies = ['view_pe', 'pe_indicators']

    def execute(self, input_data):
        ''' Execute the ViewPEDeep worker '''

        # Supplement with details indicators
        view = input_data['view_pe']
        view['indicators'] = input_data['pe_indicators']['indicator_list']
        return view

# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' view_pe_deep.py: Unit test'''

    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate input for the worker
    import os
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 
                             '../data/pe/bad/033d91aae8ad29ed9fbb858179271232')     
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'bad_pe', 'exe')
    input_data = workbench.work_request('view_pe', md5)
    input_data.update(workbench.work_request('pe_indicators', md5))

    # Execute the worker (unit test)
    worker = ViewPEDeep()
    output = worker.execute(input_data)
    print '\n<<< Unit Test >>>'
    pprint.pprint(output)

    # Execute the worker (server test)
    output = workbench.work_request('view_pe_deep', md5)
    print '\n<<< Server Test >>>'
    pprint.pprint(output)

if __name__ == "__main__":
    test()
