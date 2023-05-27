
''' Memory Image ConnScan worker. This worker utilizes the Rekall Memory Forensic Framework.
    See Google Github: http://github.com/google/rekall
    All credit for good stuff goes to them, all credit for bad stuff goes to us. :)
'''
import os
import hashlib
import pprint
import collections
from rekall_adapter.rekall_adapter import RekallAdapter

class MemoryImageConnScan(object):
    ''' This worker computes connscan-data for memory image files. '''
    dependencies = ['sample']

    def __init__(self):
        ''' Initialization '''
        self.plugin_name = 'connscan'
        self.current_table_name = 'connscan'
        self.output = {'tables': collections.defaultdict(list)}
        self.column_map = {}

    def execute(self, input_data):
        ''' Execute method '''

        # Spin up the rekall adapter
        adapter = RekallAdapter()
        adapter.set_plugin_name(self.plugin_name)
        rekall_output = adapter.execute(input_data)

        # Process the output data
        for line in rekall_output:

            if line['type'] == 'm':  # Meta
                self.output['meta'] = line['data']
            elif line['type'] == 's': # New Session (Table)
                self.current_table_name = line['data']['name'][1]
            elif line['type'] == 't': # New Table Headers (column names)
                self.column_map = {item['cname']: item['name'] if 'name' in item else item['cname'] for item in line['data']}
            elif line['type'] == 'r': # Row
                
                # Add the row to our current table
                row = RekallAdapter.process_row(line['data'], self.column_map)
                self.output['tables'][self.current_table_name].append(row)
            else:
                print 'Note: Ignoring rekall message of type %s: %s' % (line['type'], line['data'])

        # All done
        return self.output

# Unit test: Create the class, the proper input and run the execute() method for a test
import pytest
#pylint: disable=no-member
@pytest.mark.xfail
#pylint: enable=no-member
def test():
    ''' mem_connscan.py: Test '''

    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Do we have the memory forensics file?
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/memory_images/exemplar4.vmem')
    if not os.path.isfile(data_path):
        print 'Not finding exemplar4.mem... Downloading now...'
        import urllib
        urllib.urlretrieve('http://s3-us-west-2.amazonaws.com/workbench-data/memory_images/exemplar4.vmem', data_path)

    # Did we properly download the memory file?
    if not os.path.isfile(data_path):
        print 'Downloading failed, try it manually...'
        print 'wget http://s3-us-west-2.amazonaws.com/workbench-data/memory_images/exemplar4.vmem'
        exit(1)
    if os.stat(data_path).st_size < 100000:
        data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/memory_images/exemplar4.vmem') 
        with open(data_path, 'rb') as mem_file:
            print 'Corrupt memory image: %s' % mem_file.read()[:500]
        print 'Downloading failed, try it manually...'
        print 'wget http://s3-us-west-2.amazonaws.com/workbench-data/memory_images/exemplar4.vmem'
        exit(1)        

    # Store the sample
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/memory_images/exemplar4.vmem')
    with open(data_path, 'rb') as mem_file:
        raw_bytes = mem_file.read()
        md5 = hashlib.md5(raw_bytes).hexdigest()
        if not workbench.has_sample(md5):
            md5 = workbench.store_sample(open(data_path, 'rb').read(), 'exemplar4.vmem', 'mem')

    # Execute the worker (unit test)
    worker = MemoryImageConnScan()
    output = worker.execute({'sample':{'raw_bytes':raw_bytes}})
    print '\n<<< Unit Test >>>'
    print 'Meta: %s' % output['meta']
    for name, table in output['tables'].iteritems():
        print '\nTable: %s' % name
        pprint.pprint(table)
    assert 'Error' not in output

    # Execute the worker (server test)
    output = workbench.work_request('mem_connscan', md5)['mem_connscan']
    print '\n<<< Server Test >>>'
    print 'Meta: %s' % output['meta']
    for name, table in output['tables'].iteritems():
        print '\nTable: %s' % name
        pprint.pprint(table)
    assert 'Error' not in output


if __name__ == "__main__":
    test()
