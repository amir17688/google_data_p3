
''' view_pe worker '''
import pprint

class ViewPE(object):
    ''' Generates a high level summary view for PE files that incorporates a large set of workers '''
    dependencies = ['meta', 'strings', 'pe_peid', 'pe_indicators', 'pe_classifier', 'yara_sigs']

    def execute(self, input_data):
        ''' Execute the ViewPE worker '''

        # Just a small check to make sure we haven't been called on the wrong file type
        if (input_data['meta']['type_tag'] != 'exe'):
            return {'error': self.__class__.__name__+': called on '+input_data['meta']['type_tag']}

        view = {}
        view['indicators'] = list(set([item['category'] for item in input_data['pe_indicators']['indicator_list']]))
        view['peid_matches'] = input_data['pe_peid']['match_list']
        view['yara_sigs'] = input_data['yara_sigs']['matches'].keys()
        view['classification'] = input_data['pe_classifier']['classification']
        view['disass'] = self.safe_get(input_data, ['pe_disass', 'decode'])[:15]
        view.update(input_data['meta'])

        return view

    # Helper method
    @staticmethod
    def safe_get(data, key_list):
        ''' Safely access dictionary keys when plugin may have failed '''
        for key in key_list:
            data = data.get(key, {})
        return data if data else 'plugin_failed'

# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' view_pe.py: Unit test'''

    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate input for the worker
    import os
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 
                             '../data/pe/bad/cc113aa59c04b17e7cb832fc417f104d')     
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'bad_pe', 'exe')
    input_data = workbench.work_request('meta', md5)
    input_data.update(workbench.work_request('strings', md5))
    input_data.update(workbench.work_request('pe_peid', md5))
    input_data.update(workbench.work_request('pe_indicators', md5))
    input_data.update(workbench.work_request('pe_classifier', md5))
    input_data.update(workbench.work_request('yara_sigs', md5))

    # Execute the worker (unit test)
    worker = ViewPE()
    output = worker.execute(input_data)
    print '\n<<< Unit Test >>>'
    pprint.pprint(output)

    # Execute the worker (server test)
    output = workbench.work_request('view_pe', md5)
    print '\n<<< Server Test >>>'
    pprint.pprint(output)

if __name__ == "__main__":
    test()
