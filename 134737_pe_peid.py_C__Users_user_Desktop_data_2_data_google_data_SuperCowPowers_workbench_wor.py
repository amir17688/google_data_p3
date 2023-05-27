"""This client looks for PEid signatures in PE Files."""

import zerorpc
import os
import pprint
import client_helper

def run():
    """This client looks for PEid signatures in PE Files."""
    
    # Grab server args
    args = client_helper.grab_server_args()

    # Start up workbench connection
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect('tcp://'+args['server']+':'+args['port'])

    # Test out PEFile -> peid
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../data/pe/bad')
    file_list = [os.path.join(data_path, child) for child in os.listdir(data_path)][:2]
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../data/pe/good')
    file_list += [os.path.join(data_path, child) for child in os.listdir(data_path)][:2]
    for filename in file_list:

        # Skip OS generated files
        if '.DS_Store' in filename: continue

        with open(filename,'rb') as f:
            base_name = os.path.basename(filename)
            md5 = workbench.store_sample(f.read(), base_name, 'exe')
            results = workbench.work_request('pe_peid', md5)
            pprint.pprint(results)


def test():
    """Executes pe_peid test."""
    run()

if __name__ == '__main__':
    run()
