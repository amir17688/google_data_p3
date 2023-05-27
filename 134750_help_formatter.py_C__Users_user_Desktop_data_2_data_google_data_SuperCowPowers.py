
''' HelpFormatter worker '''

from IPython.utils.coloransi import TermColors as color
#pylint: disable=no-member

class HelpFormatter(object):
    ''' This worker does CLI formatting and coloring for any help object '''
    dependencies = ['help_base']

    def execute(self, input_data):
        ''' Do CLI formatting and coloring based on the type_tag '''
        input_data = input_data['help_base']
        type_tag = input_data['type_tag']

        # Standard help text
        if type_tag == 'help':
            output = '%s%s%s' % (color.LightBlue, input_data['help'], color.Normal)

        # Worker
        elif type_tag == 'worker':
            output = '%s%s' % (color.Yellow, input_data['name'])
            output += '\n    %sInput: %s%s%s' % (color.LightBlue, color.Green, input_data['dependencies'], color.Normal)
            output += '\n    %s%s' % (color.Green, input_data['docstring'])

        # Command
        elif type_tag == 'command':
            output = '%s%s%s %s' % (color.Yellow, input_data['command'], color.LightBlue, input_data['sig'])
            output += '\n    %s%s%s' % (color.Green, input_data['docstring'], color.Normal)

        # WTF: Alert on unknown type_tag and return a string of the input_data
        else:
            print 'Alert: help_formatter worker received malformed object: %s' % str(input_data)
            output = '\n%s%s%s' % (color.Red, str(input_data), color.Normal)

        # Return the formatted and colored help
        return {'help': output}

# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' help_formatter.py: Unit test'''

    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate input for the worker
    input_data1 = workbench.work_request('help_base', 'workbench')
    input_data2 = workbench.work_request('help_base', 'meta')
    input_data3 = workbench.work_request('help_base', 'store_sample')

    # Execute the worker (unit test)
    worker = HelpFormatter()
    output = worker.execute(input_data1)
    print '\n<<< Unit Test >>>'
    print output['help']
    output = worker.execute(input_data2)
    print '\n<<< Unit Test >>>'
    print output['help']
    output = worker.execute(input_data3)
    print '\n<<< Unit Test >>>'
    print output['help']      

    # Execute the worker (server test)
    output = workbench.work_request('help_formatter', 'meta')
    print '\n<<< Server Test >>>'
    print output['help_formatter']['help']

if __name__ == "__main__":
    test()
