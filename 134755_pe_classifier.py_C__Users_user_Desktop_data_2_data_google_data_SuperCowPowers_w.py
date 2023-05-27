
''' PEClassifier worker (just a placeholder, not a real classifier at this point) '''

class PEClassifier(object):
    ''' This worker classifies PEFiles as Evil or AOK  (TOY not a real classifier at this point)'''
    dependencies = ['pe_features', 'pe_indicators']

    def __init__(self):
        ''' Initialization '''
        self.output = {'classification':'Toy/Fake Classifier says AOK!'}

    def execute(self, input_data):
        ''' This worker classifies PEFiles as Evil or AOK  (TOY not a real classifier at this point)'''

        # In general you'd do something different with these two outputs
        # for this toy example will just smash them in a big string
        pefile_output = input_data['pe_features']
        indicators = input_data['pe_indicators']
        all_input = str(pefile_output) + str(indicators)

        flag = 'Reported Checksum does not match actual checksum'
        if flag in all_input:
            self.output['classification'] = 'Toy/Fake Classifier says Evil!'

        return self.output

# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' pe_classifier.py: Unit test'''
    import pprint

    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate the input data for this worker
    import os
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../data/pe/bad/033d91aae8ad29ed9fbb858179271232')
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'bad_pe', 'exe')
    input_data = workbench.work_request('pe_features', md5)
    input_data.update(workbench.work_request('pe_indicators', md5))

    # Execute the worker (unit test)
    worker = PEClassifier()
    output = worker.execute(input_data)
    print '\n<<< Unit Test >>>'
    pprint.pprint(output)

    # Execute the worker (server test)
    output = workbench.work_request('pe_classifier', md5)
    print '\n<<< Server Test >>>'
    pprint.pprint(output)

if __name__ == "__main__":
    test()
