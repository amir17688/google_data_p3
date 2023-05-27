
''' view_pdf worker '''
import pprint

class ViewPDF(object):
    ''' ViewPDF: Generates a view for PDF files '''
    dependencies = ['meta', 'strings']

    def execute(self, input_data):
        ''' Execute the ViewPDF worker '''

        # Just a small check to make sure we haven't been called on the wrong file type
        if (input_data['meta']['type_tag'] != 'pdf'):
            return {'error': self.__class__.__name__+': called on '+input_data['meta']['type_tag']}

        view = {}
        view['strings'] = input_data['strings']['string_list'][:5]
        view.update(input_data['meta'])
        return view

# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    '''' view_pdf.py: Unit test'''
    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate input for the worker
    import os
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../data/pdf/bad/067b3929f096768e864f6a04f04d4e54')
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'bad_pdf', 'pdf')
    input_data = workbench.work_request('meta', md5)
    input_data.update(workbench.work_request('strings', md5))

    # Execute the worker (unit test)
    worker = ViewPDF()
    output = worker.execute(input_data)
    print '\n<<< Unit Test >>>'
    pprint.pprint(output)
    
    # Execute the worker (server test)
    output = workbench.work_request('view_pdf', md5)
    print '\n<<< Server Test >>>'
    pprint.pprint(output)

if __name__ == "__main__":
    test()
