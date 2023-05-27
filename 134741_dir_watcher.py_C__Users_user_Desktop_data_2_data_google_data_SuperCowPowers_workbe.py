""" A simple directory watcher 
    Credit: ronedg @ http://stackoverflow.com/questions/182197/how-do-i-watch-a-file-for-changes-using-python
"""
import os, time
import gevent

class DirWatcher(object):
    """ A simple directory watcher """
    
    def __init__(self, path):
        """ Initialize the Directory Watcher
        Args:
            path: path of the directory to watch
        """
        self.path = path
        self.on_create = None
        self.on_modify = None
        self.on_delete = None
        self.jobs = None

    def register_callbacks(self, on_create, on_modify, on_delete):
        """ Register callbacks for file creation, modification, and deletion """
        self.on_create = on_create
        self.on_modify = on_modify
        self.on_delete = on_delete

    def start_monitoring(self):
        """ Monitor the path given """
        self.jobs = [gevent.spawn(self._start_monitoring)]

    def _start_monitoring(self):
        """ Internal method that monitors the directory for changes """
        
        # Grab all the timestamp info
        before = self._file_timestamp_info(self.path)

        while True:
            gevent.sleep(1)
            after = self._file_timestamp_info(self.path)

            added = [fname for fname in after.keys() if fname not in before.keys()]
            removed = [fname for fname in before.keys() if fname not in after.keys()]
            modified = []

            for fname in before.keys():
                if fname not in removed:
                    if os.path.getmtime(fname) != before.get(fname):
                        modified.append(fname)

            if added: 
                self.on_create(added)
            if removed: 
                self.on_delete(removed)
            if modified: 
                self.on_modify(modified)
    
            before = after

    def _file_timestamp_info(self, path):
        """ Grab all the timestamps for the files in the directory """
        files = [os.path.join(path, fname) for fname in os.listdir(path) if '.py' in fname]
        return dict ([(fname, os.path.getmtime(fname)) for fname in files])

    def __del__(self):
        """ Cleanup the DirWatcher instance """
        gevent.joinall(self.jobs)
