
''' PE SSDeep Similarity worker '''

import os
import ssdeep as ssd
import zerorpc
import pprint
from operator import itemgetter

class PEDeepSim(object):
    ''' This worker computes fuzzy matches between samples with ssdeep '''
    dependencies = ['meta_deep']

    def __init__(self):
        self.workbench = zerorpc.Client(timeout=300, heartbeat=60)
        self.workbench.connect("tcp://127.0.0.1:4242")

    def execute(self, input_data):
        ''' Execute method '''
        my_ssdeep = input_data['meta_deep']['ssdeep']
        my_md5 = input_data['meta_deep']['md5']

        # For every PE sample in the database compute my ssdeep fuzzy match
        sample_set = self.workbench.generate_sample_set('exe')
        results = self.workbench.set_work_request('meta_deep', sample_set, ['md5','ssdeep'])
        sim_list = []
        for result in results:
            if result['md5'] != my_md5:
                sim_list.append({'md5':result['md5'], 'sim':ssd.compare(my_ssdeep, result['ssdeep'])})

        # Sort and return the sim_list (with some logic for threshold)
        sim_list.sort(key=itemgetter('sim'), reverse=True)
        output_list = [sim for sim in sim_list if sim['sim'] > 0]
        return {'md5': my_md5, 'sim_list':output_list}

    def __del__(self):
        ''' Class Cleanup '''
        # Close zeroRPC client
        self.workbench.close()

# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' pe_deep_sim.py: Unit test '''

    # This worker test requires a local server running
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate input for the worker
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../data/pe/bad/033d91aae8ad29ed9fbb858179271232')
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'bad_pe', 'exe')
    input_data = workbench.work_request('meta_deep', md5)

    # Execute the worker (unit test)
    worker = PEDeepSim()
    output = worker.execute(input_data)
    print '\n<<< Unit Test >>>'
    pprint.pprint(output)

    # Execute the worker (server test)
    output = workbench.work_request('pe_deep_sim', md5)
    print '\n<<< Server Test >>>'
    pprint.pprint(output)

if __name__ == "__main__":
    test()
