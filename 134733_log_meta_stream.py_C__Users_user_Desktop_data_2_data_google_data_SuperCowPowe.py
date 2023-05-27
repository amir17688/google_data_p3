"""This client gets metadata about log files."""

import zerorpc
import os
import pprint
import client_helper

def run():
    """This client gets metadata about log files."""
    
    # Grab server args
    args = client_helper.grab_server_args()
    
    # Start up workbench connection
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect('tcp://'+args['server']+':'+args['port'])

    # Test out some log files
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../data/log')
    file_list = [os.path.join(data_path, child) for child in os.listdir(data_path)]
    for filename in file_list:
        with open(filename,'rb') as f:

            # Skip OS generated files
            base_name = os.path.basename(filename)
            if base_name == '.DS_Store': continue

            md5 = workbench.store_sample(f.read(), base_name, 'log')
            results = workbench.work_request('view_log_meta', md5)
            print 'Filename: %s\n' % (base_name)
            pprint.pprint(results)
            stream_log = workbench.stream_sample(md5, {'max_rows':20})
            for row in stream_log:
                print row

def test():
    """Executes log_meta_stream test."""
    run()

if __name__ == '__main__':
    run()

