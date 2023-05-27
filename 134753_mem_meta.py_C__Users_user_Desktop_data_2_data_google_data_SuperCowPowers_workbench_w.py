
''' Memory Image Meta worker. This worker utilizes the Rekall Memory Forensic Framework.
    See Google Github: http://github.com/google/rekall
    All credit for good stuff goes to them, all credit for bad stuff goes to us. :)
    Note: In general this code is crazy, because Rekall has it's own type system
          we're scraping it's output and trying to squeeze stuff into general python types.
'''
import os
import hashlib
import pprint
import collections
from rekall_adapter.rekall_adapter import RekallAdapter


class MemoryImageMeta(object):
    ''' This worker computes meta-data for memory image files. '''
    dependencies = ['sample']

    def __init__(self):
        ''' Initialization '''
        self.plugin_name = 'imageinfo'
        self.current_table_name = 'info'
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
    ''' mem_meta.py: Test '''

    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Store the sample
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/memory_images/exemplar4.vmem')
    with open(data_path, 'rb') as mem_file:
        raw_bytes = mem_file.read()
        md5 = hashlib.md5(raw_bytes).hexdigest()
        if not workbench.has_sample(md5):
            md5 = workbench.store_sample(open(data_path, 'rb').read(), 'exemplar4.vmem', 'mem')

    # Execute the worker (unit test)
    worker = MemoryImageMeta()
    output = worker.execute({'sample':{'raw_bytes':raw_bytes}})
    print '\n<<< Unit Test >>>'
    print 'Meta: %s' % output['meta']
    for name, table in output['tables'].iteritems():
        print '\nTable: %s' % name
        pprint.pprint(table)
    assert 'Error' not in output

    # Execute the worker (server test)
    output = workbench.work_request('mem_meta', md5)['mem_meta']
    print '\n<<< Server Test >>>'
    print 'Meta: %s' % output['meta']
    for name, table in output['tables'].iteritems():
        print '\nTable: %s' % name
        pprint.pprint(table)
    assert 'Error' not in output


if __name__ == "__main__":
    test()
