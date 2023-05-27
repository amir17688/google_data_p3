''' This client calls a bunch of help commands from workbench '''
import zerorpc
import client_helper

def run():
    ''' This client calls a bunch of help commands from workbench '''
    
    # Grab server args
    args = client_helper.grab_server_args()

    # Start up workbench connection
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect('tcp://'+args['server']+':'+args['port'])

    # Call help methods
    print workbench.help()
    print workbench.help('basic')
    print workbench.help('commands')
    print workbench.help('store_sample')
    print workbench.help('workers')
    print workbench.help('meta')

    # Call a test worker
    print workbench.test_worker('meta')
    

def test():
    ''' help_client test '''
    run()

if __name__ == '__main__':
    run()

