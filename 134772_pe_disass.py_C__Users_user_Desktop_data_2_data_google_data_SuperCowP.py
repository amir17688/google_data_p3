
''' PE Disass worker '''
from disass.Disass32 import Disass32

def plugin_info():
    return {'name': 'pe_disass', 'class':'Disass', 'dependencies': ['sample'],
            'description': '(Beta) This worker does disassembly on a sample. Output keys: [decode]'}


class Disass():

    def execute(self, input_data):
        raw_bytes = input_data['sample']['raw_bytes']
        try:
            disass = Disass32(data=raw_bytes)
        except Exception, error:
            return {'decode': [str(error)]}
        return {'decode': disass.decode}


# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' pe_disass.py: Unit test'''
    worker = Disass()
    output = worker.execute({'sample': 
        {'raw_bytes':open('../data/pe/bad/033d91aae8ad29ed9fbb858179271232', 'rb').read()}})
    print 'Disass: %s ' % str(output['decode'][:50])  # Truncate for now

if __name__ == "__main__":
    test()
