''' Spin up Workbench Server (this is a singleton module)'''

import multiprocessing
import workbench.server.workbench_server as workbench_server

print '\nStarting up the Workbench server...'
process = multiprocessing.Process(target=workbench_server.run)
process.start()

def shutdown():
    # Terminate the workbench server process
    print '\nShutting down the Workbench server...'
    try:
        process.terminate()
    except OSError, error:
        print 'Not able to shut down server, probably means another one is running...'
        print 'Error %s' % error
