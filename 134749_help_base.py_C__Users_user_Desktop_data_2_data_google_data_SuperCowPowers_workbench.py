
''' HelpBase worker '''

class HelpBase(object):
    ''' This worker computes help for any 'info' object '''
    dependencies = ['info']

    def execute(self, input_data):
        """ Info objects all have a type_tag of ('help','worker','command', or 'other') """
        input_data = input_data['info']
        type_tag = input_data['type_tag']
        if type_tag == 'help':
            return {'help': input_data['help'], 'type_tag': input_data['type_tag']}
        elif type_tag == 'worker':
            out_keys = ['name', 'dependencies', 'docstring', 'type_tag'] 
            return {key: value for key, value in input_data.iteritems() if key in out_keys}
        elif type_tag == 'command':
            out_keys = ['command', 'sig', 'docstring', 'type_tag']
            return {key: value for key, value in input_data.iteritems() if key in out_keys}
        elif type_tag == 'other':
            return input_data
        else:
            print 'Got a malformed info object %s' % input_data
            return input_data

# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' help.py: Unit test'''

    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate input for the worker
    input_data = workbench.get_info('meta')

    # Execute the worker (unit test)
    worker = HelpBase()
    output = worker.execute(input_data)
    print '\n<<< Unit Test >>>'
    print output

    # Execute the worker (server test)
    output = workbench.work_request('help_base', 'meta')
    print '\n<<< Server Test >>>'
    print output['help_base']

if __name__ == "__main__":
    test()
