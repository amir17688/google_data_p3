
import pygtail
import contextlib
import os, time
import tempfile
import shutil

@contextlib.contextmanager
def make_temp_directory():
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)

@contextlib.contextmanager
def make_temp_file():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        name = f.name
    try:
        yield name
    finally:
        os.unlink(name)

def tail_file(filename):
    ''' Tail a file using pygtail. Note: this could probably be improved '''
    with make_temp_file() as offset_file:
        while True:
            for line in pygtail.Pygtail(filename, offset_file=offset_file):
                yield line
            time.sleep(1.0)    
    

# Unit test: Test out the functionality on the syslog file
def test():
    
    for line in tail_file('/var/log/system.log'):
        print line

if __name__ == "__main__":
    test()
