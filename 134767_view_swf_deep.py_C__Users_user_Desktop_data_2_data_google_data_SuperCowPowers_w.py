
''' view_swf_deep worker '''
import pprint

class ViewSWFDeep(object):
    ''' ViewSWFDeep: Generates a view for SWF files '''
    dependencies = ['view_swf']

    def execute(self, input_data):
        ''' Execute the ViewSWFDeep worker '''
        view = input_data['view_swf']
        return view

# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    '''' view_swf_deep.py: Unit test'''
    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate input for the worker
    import os
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/swf/unknown.swf')
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'unknown.swf', 'swf')
    input_data = workbench.work_request('view_swf', md5)

    # Execute the worker (unit test)
    worker = ViewSWFDeep()
    output = worker.execute(input_data)
    print '\n<<< Unit Test >>>'
    pprint.pprint(output)
    
    # Execute the worker (server test)
    output = workbench.work_request('view_swf_deep', md5)
    print '\n<<< Server Test >>>'
    pprint.pprint(output)

if __name__ == "__main__":
    test()
