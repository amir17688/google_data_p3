''' PcapSetBro worker '''
import os
import pcap_bro

class PcapSetBro(pcap_bro.PcapBro):
    ''' This worker runs Bro scripts on a set of pcap files '''
    dependencies = ['sample_set']

    def pcap_inputs(self, input_data):
        
        # For PcapSetBro the input_data is expected to be set of md5s
        # Setup handles for the set of md5s.
        filenames = []
        for md5 in input_data['sample_set']['md5_list']:
            sample = self.workbench.get_sample(md5)['sample']
            raw_bytes = sample['raw_bytes']
            filename = os.path.basename(sample['filename'])
            with open(filename,'wb') as pcap_file:
                pcap_file.write(raw_bytes)
                filenames.append(filename)
        return filenames


# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' pcap_set_bro.py: Unit test'''
    # This worker test requires a local server as it relies on the recursive dependencies
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Open a bunch of pcaps
    data_dir = '../data/pcap'
    file_list = [os.path.join(data_dir, child) for child in os.listdir(data_dir)]
    pcap_md5s = []
    for filename in file_list:

        # Skip OS generated files
        if '.DS_Store' in filename: continue        

        with open(filename,'rb') as f:
            base_name = os.path.basename(filename)
            pcap_md5s.append(workbench.store_sample(f.read(), base_name, 'pcap'))

    # Now store the sample set
    set_md5 = workbench.store_sample_set(pcap_md5s)
    print set_md5

    # Execute the worker (unit test)
    worker = PcapSetBro()
    output = worker.execute({'sample_set':{'md5_list':pcap_md5s}})
    print '\n<<< Unit Test >>>'
    import pprint
    pprint.pprint(output)

    # Execute the worker (server test)
    output = workbench.work_request('pcap_set_bro', set_md5)
    print '\n<<< Server Test >>>'
    import pprint
    pprint.pprint(output)


if __name__ == "__main__":
    test()
