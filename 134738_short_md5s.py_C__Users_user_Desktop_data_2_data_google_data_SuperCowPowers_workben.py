"""This client tests workbench support for short md5s """

import zerorpc
import os
import pprint
import client_helper

def run():
    """This client tests workbench support for short md5s """
    
    # Grab server args
    args = client_helper.grab_server_args()

    # Start up workbench connection
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect('tcp://'+args['server']+':'+args['port'])

    # Pull in a bunch of files
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../data/pe/bad')
    file_list = [os.path.join(data_path, child) for child in os.listdir(data_path)]
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../data/pe/good')
    file_list += [os.path.join(data_path, child) for child in os.listdir(data_path)]
    for filename in file_list:

        # Skip OS generated files
        if '.DS_Store' in filename: continue

        with open(filename,'rb') as f:
            base_name = os.path.basename(filename)
            md5 = workbench.store_sample(f.read(), base_name, 'exe')
            results = workbench.work_request('meta', md5[:6])
            pprint.pprint(results)

import pytest
#pylint: disable=no-member
@pytest.mark.xfail
#pylint: enable=no-member
def test():
    """Executes short md5 test."""
    run()

if __name__ == '__main__':
    run()
