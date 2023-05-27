import os
import sys
import imp
import pickle
import traceback
import md5
from collections import namedtuple

Result = namedtuple('Result', ['type', 'content'])
choco = None
module = None
modules = []

def init_module(cc, ep):
    global choco, module
    choco = cc
    module = ep

def dispatch(room, message):
    choco.dispatch(room, message, True)

def module_loader(home, config):
    for fn in os.listdir(os.path.join(home, 'modules')):
        name = os.path.basename(fn)[:-3]
        if name in config.EXCLUDED_MODULES: continue
        if fn.endswith('.py') and not fn.startswith('_'):
            fn = os.path.join(os.path.dirname(os.path.realpath(__file__)), fn)
            try: modules.append(imp.load_source(name, fn))
            except Exception, e:
                traceback.print_exc()
                print >> sys.stderr, "Error loading %s: %s" % (name, e)
                sys.exit(1)
