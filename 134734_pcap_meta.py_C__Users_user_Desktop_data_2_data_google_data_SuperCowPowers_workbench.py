"""This client pulls PCAP meta data."""

import zerorpc
import os
import pprint
import client_helper

def run():
    """This client pulls PCAP meta data."""
    
    # Grab server args
    args = client_helper.grab_server_args()

    # Start up workbench connection
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect('tcp://'+args['server']+':'+args['port'])

    # Test out PCAP data
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../data/pcap')
    file_list = [os.path.join(data_path, child) for child in os.listdir(data_path)]
    for filename in file_list:

        # Skip OS generated files
        if '.DS_Store' in filename: continue

        with open(filename,'rb') as f:
            base_name = os.path.basename(filename)
            md5 = workbench.store_sample(f.read(), base_name, 'pcap')
            results = workbench.work_request('view_pcap', md5)
            print 'Filename: %s results:' % (base_name)
            pprint.pprint(results)

def test():
    """Executes pcap_meta test."""
    run()

if __name__ == '__main__':
    run()

