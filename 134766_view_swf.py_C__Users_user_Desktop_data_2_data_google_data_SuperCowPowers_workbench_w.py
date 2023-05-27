
''' view_swf worker '''
import pprint

class ViewSWF(object):
    ''' ViewSWF: Generates a view for SWF files '''
    dependencies = ['swf_meta', 'strings']

    def execute(self, input_data):
        ''' Execute the ViewSWF worker '''

        # Just a small check to make sure we haven't been called on the wrong file type
        if (input_data['swf_meta']['type_tag'] != 'swf'):
            return {'error': self.__class__.__name__+': called on '+input_data['swf_meta']['type_tag']}

        view = input_data['swf_meta']
        view['strings'] = input_data['strings']['string_list'][:5]
        return view

# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    '''' view_swf.py: Unit test'''
    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate input for the worker
    import os
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/swf/unknown.swf')
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'unknown.swf', 'swf')
    input_data = workbench.work_request('swf_meta', md5)
    input_data.update(workbench.work_request('strings', md5))

    # Execute the worker (unit test)
    worker = ViewSWF()
    output = worker.execute(input_data)
    print '\n<<< Unit Test >>>'
    pprint.pprint(output)
    
    # Execute the worker (server test)
    output = workbench.work_request('view_swf', md5)
    print '\n<<< Server Test >>>'
    pprint.pprint(output)

if __name__ == "__main__":
    test()
