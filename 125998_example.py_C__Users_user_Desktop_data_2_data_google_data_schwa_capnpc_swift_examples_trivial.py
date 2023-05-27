#!/usr/bin/env python

__author__ = 'schwa'

import sys
import capnp

# capnp decode schema.capnp CodeGeneratorRequest < dump.dat

capnp.remove_import_hook()
example = capnp.load('example.capnp')

#print 'DONE'

# d = sys.stdin.read()
# file('dump.dat', 'w').write(d)

thing = example.Thing.new_message()
thing.value = 0xDEADBEEF

f = file('example.dat','w')
thing.write(f)
# capnp decode ../example.capnp Thing < example.dat
