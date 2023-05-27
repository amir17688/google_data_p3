''' PE peid worker, uses the peid_userdb.txt database of signatures '''
import os
import peutils
import pefile
import pkg_resources
import pprint

# We want to load this once per module load
def get_peid_db():
    ''' Grab the peid_userdb.txt file from local disk '''

    # Try to find the yara rules directory relative to the worker
    my_dir = os.path.dirname(os.path.realpath(__file__))
    db_path = os.path.join(my_dir, 'peid_userdb.txt')
    if not os.path.exists(db_path):
        raise RuntimeError('peid could not find peid_userdb.txt under: %s' % db_path)

    # Okay load up signature
    signatures = peutils.SignatureDatabase(data = open(db_path, 'rb').read())
    return signatures

PEID_SIGS = get_peid_db()

class PEIDWorker(object):
    ''' This worker looks up pe_id signatures for a PE file. '''
    dependencies = ['sample']

    def __init__(self):
        self.peid_sigs = PEID_SIGS

    def execute(self, input_data):
        ''' Execute the PEIDWorker '''
        raw_bytes = input_data['sample']['raw_bytes']

        # Have the PE File module process the file
        try:
            pefile_handle = pefile.PE(data=raw_bytes, fast_load=False)
        except (AttributeError, pefile.PEFormatError), error:
            return {'error':  str(error), 'match_list': []}

        # Now get information from PEID module
        peid_match = self.peid_features(pefile_handle)
        return {'match_list': peid_match}

    def peid_features(self, pefile_handle):
        ''' Get features from PEid signature database'''
        peid_match = self.peid_sigs.match(pefile_handle)
        return peid_match if peid_match else []


# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' pe_peid.py: Unit test'''

    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate input for the worker
    import os
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../data/pe/bad/86714940f491bc38c2e842e80c7f778e')
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'bad_pe', 'exe')
    input_data = workbench.get_sample(md5)

    # Execute the worker (unit test)
    worker = PEIDWorker()
    output = worker.execute(input_data)
    print '\n<<< Unit Test >>>'
    pprint.pprint(output)

    # Execute the worker (server test)
    output = workbench.work_request('pe_peid', md5)
    print '\n<<< Server Test >>>'
    pprint.pprint(output)

if __name__ == "__main__":
    test()
