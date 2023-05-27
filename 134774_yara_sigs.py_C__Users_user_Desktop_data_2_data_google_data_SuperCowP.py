
''' Yara worker '''
import zerorpc
import os
import yara
import pprint
import collections
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class YaraSigs(object):
    ''' This worker check for matches against yara sigs. 
        Output keys: [matches:list of matches] '''
    dependencies = ['sample']

    def __init__(self):
        self.workbench = zerorpc.Client(timeout=300, heartbeat=60)
        self.workbench.connect("tcp://127.0.0.1:4242") 

        # Check if Workbench has compiled rules
        self.rules = self.get_rules_from_workbench()
        if not self.rules:
            self.rules = self.get_rules_from_disk()

    def get_rules_from_workbench(self):
        samples = self.workbench.generate_sample_set('yara_rules')
        if not samples:
            return None
        elif len(samples)>1:
            print 'Error: More than one yara rule set!'
            exit(1)
        else:
            return yara.load(self.workbench.get_sample[samples[0]])

    def save_rules_to_workbench(self, rules):

        # Remove any old rule sets
        samples = self.workbench.generate_sample_set('yara_rules')
        if samples:
            for sample in samples:
                remove_sample(sample)

        # Save rule set
        mem_file = StringIO()
        self.rules.save(mem_file)
        mem_file.seek(0)
        self.workbench.save_sample(mem_file.read(), 'yara_rules')        
            
    def get_rules_from_disk(self):
        ''' Recursively traverse the yara/rules directory for rules '''

        # Try to find the yara rules directory relative to the worker
        my_dir = os.path.dirname(os.path.realpath(__file__))
        yara_rule_path = os.path.join(my_dir, 'yara/rules')
        if not os.path.exists(yara_rule_path):
            raise RuntimeError('yara could not find yara rules directory under: %s' % my_dir)

        # Okay load in all the rules under the yara rule path
        self.rules = yara.load_rules(rules_rootpath=yara_rule_path)

        # Save rules to Workbench
        self.save_rules_to_workbench(self.rules)

        return self.rules

    def execute(self, input_data):
        ''' yara worker execute method '''
        raw_bytes = input_data['sample']['raw_bytes']
        matches = self.rules.match_data(raw_bytes)

        # The matches data is organized in the following way
        # {'filename1': [match_list], 'filename2': [match_list]}
        # match_list = list of match
        # match = {'meta':{'description':'blah}, tags=[], matches:True,
        #           strings:[string_list]}
        # string = {'flags':blah, 'identifier':'$', 'data': FindWindow, 'offset'}
        # 
        # So we're going to flatten a bit (shrug)
        # {filename_match_meta_description: string_list}
        flat_data = collections.defaultdict(list)
        for filename, match_list in matches.iteritems():
            for match in match_list:
                if 'description' in match['meta']:
                    new_tag = filename+'_'+match['meta']['description']
                else:
                    new_tag = filename+'_'+match['rule']
                for match in match['strings']:
                    flat_data[new_tag].append(match['data'])
                # Remove duplicates
                flat_data[new_tag] = list(set(flat_data[new_tag]))

        return {'matches': flat_data}


# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' yara_sigs.py: Unit test'''

    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Test a file with known yara sigs
    filename = '../data/pe/bad/auriga.exe'

    with open(filename,'rb') as pe_file:
        base_name = os.path.basename(filename)
        md5 = workbench.store_sample(pe_file.read(), base_name, 'exe')

    # Grab the sample from workbench
    input_data = workbench.get_sample(md5)


    # Execute the worker (unit test)
    worker = YaraSigs()
    output = worker.execute(input_data)
    print '\n<<< Unit Test >>>'
    pprint.pprint(output)

    # Execute the worker (server test)
    output = workbench.work_request('yara_sigs', md5)
    print '\n<<< Server Test >>>'
    pprint.pprint(output)

if __name__ == "__main__":
    test()
