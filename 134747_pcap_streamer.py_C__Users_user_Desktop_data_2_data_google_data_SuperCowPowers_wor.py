
from gevent import monkey; monkey.patch_all(thread=False)
import zerorpc
import os, sys
import argparse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import tempfile
import shutil
import subprocess

class DirWatcher(FileSystemEventHandler):
    ''' Watches a directory and calls the callback when files are created '''

    def __init__(self, data_dir, callback):
        ''' Initialization '''
        self.callback = callback

        # Now setup dynamic monitoring of the data directory
        observer = Observer()
        observer.schedule(self, path=data_dir)
        observer.start()

    def on_created(self, event):
        ''' File created '''
        self.callback(event.src_path)


class TCPDumpToWorkbench(object):
    ''' This is a very specific tcpdump to workbench client. '''

    def __init__(self, listen=False):
        ''' Initialization '''

        # Setup directories
        self.orig_dir = os.getcwd()
        self.temp_dir = None

        # This command will create two files workbench.pcap[0-1]
        if (listen):
            self.tcpdump_cmd = 'tcpdump -I -P -i en0 -C 1 -s 0 -k NP -W 2 -w workbench.pcap'
        else:
            self.tcpdump_cmd = 'tcpdump -i en0 -C 1 -s 0 -k NP -W 2 -w workbench.pcap'
        self.tcpdump_process = None
        self.pcap_index = 0

        # The logic here is a bit odd, we have an 'on-deck' pcap file
        # and when a new pcap file is created the on-deck one is considered
        # finished, sent to workbench and then deleted
        self.on_deck = None

        # Report the tcpdump command being used
        print 'Capturing with: %s' % self.tcpdump_cmd

    def __enter__(self):
        ''' Return self (with statement idiom) '''
        return self

    def execute(self):
        ''' Begin capturing PCAPs and sending them to workbench '''

        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)

        # Spin up the directory watcher
        DirWatcher(self.temp_dir, self.file_created)

        # Spin up tcpdump
        self.subprocess_manager(self.tcpdump_cmd)

    def file_created(self, filepath):
        ''' File created callback '''

        # Send the on-deck pcap to workbench
        if self.on_deck:
            self.store_file(self.on_deck)
            os.remove(self.on_deck)

        # Now put the newly created file on-deck
        self.on_deck = filepath

    def store_file(self, filename):
        ''' Store a file into workbench '''
        
        # Spin up workbench
        self.workbench = zerorpc.Client(timeout=300, heartbeat=60)
        self.workbench.connect("tcp://127.0.0.1:4242")   

        # Open the file and send it to workbench
        storage_name = "streaming_pcap" + str(self.pcap_index)
        print filename, storage_name
        with open(filename,'rb') as f:
            self.workbench.store_sample(f.read(), storage_name, 'pcap')
        self.pcap_index += 1

        # Close workbench client
        self.workbench.close()

    def subprocess_manager(self, exec_args):
        try:
            self.tcpdump_process = subprocess.Popen(exec_args.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError:
            raise RuntimeError('Could not run tcpdump executable (either not \
                               installed or not in path): %s' % (exec_args))
        out, err = self.tcpdump_process.communicate()
        if out:
            print 'standard output of subprocess: %s' % out
        if err:
            raise RuntimeError('%s\ntcpdump had output on stderr: %s' % (exec_args, err))
        if self.tcpdump_process.returncode:
            raise RuntimeError('%s\ntcpdump had returncode: %d' % (exec_args, self.tcpdump_process.returncode))

    def __exit__(self, func_type, value, traceback):
        ''' Class Cleanup '''
        print '\nTCP Dumper.. Cleaning up :)'

        # Terminate the tcpdump process
        self.tcpdump_process.kill()

        # Change back to original directory
        os.chdir(self.orig_dir)

        # Clean up the temporary directory
        shutil.rmtree(self.temp_dir)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=4242, help='port used by workbench server')
    parser.add_argument('-s', '--server', type=str, default='tcp://127.0.0.1', help='location of workbench server')
    parser.add_argument('-l', '--listen', dest='listen', default=False, action='store_true', help='listen/monitor mode')
    args = parser.parse_args()
    port = str(args.port)
    server = str(args.server)
    listen = args.listen

    # Print out informative message
    print 'Dumping PCAPs to Workbench server. Use ^C to stop this script...'

    # Spin up workbench client
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect(server+':'+port)

    # Spin up our tcpdumper
    try:
        with TCPDumpToWorkbench(listen) as dumper:
            dumper.execute()
    except KeyboardInterrupt:
        print 'Exiting...'
        sys.exit()    


def test():
    ''' pcap_streamer test '''
    main()

if __name__ == '__main__':
    main()
