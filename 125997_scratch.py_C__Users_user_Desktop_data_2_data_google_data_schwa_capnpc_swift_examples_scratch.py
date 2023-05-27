__author__ = 'schwa'

import subprocess
import os

from pathlib import Path
import capnp

capnp.remove_import_hook()

schema = """
@0xe08cb8640e0d7173;

struct ExampleStruct {
    example0 @0 :Text = "Hello world";
    example1 @1 :List(Int32) = [1,2,3];
    example2 @2 :List(Int8);
    example3 @3 :NestedStruct;

    struct NestedStruct {
        exampleInt1 @0 :Int32;
    }
}
"""

# Save schema to disk
schema_path = Path("scratch.capnp")
schema_path.open("w").write(unicode(schema))

# Load schema
schema = capnp.load(str(schema_path))

# Produce demo message.
msg = schema.ExampleStruct.new_message()
msg.example0 = "Banana"
msg.example1 = [1,2,3]
msg.example2 = [3,2,1]
msg.example3 = schema.ExampleStruct.NestedStruct.new_message()
msg.example3.exampleInt1 = 42

# Write serialized message to disk
msg.write(Path("scratch.dat").open("wb"))

# Dump the schema
output = subprocess.check_output(["capnp", "compile", "scratch.capnp", "-ocapnp"])
Path("scratch.structure.capnp").open("w").write(unicode(output))

# Produce the .swift files.
env = dict(os.environ)
env['PATH'] = env['PATH'] + ":/Users/schwa/.virtualenvs/dev/bin/"
output = subprocess.check_output(["capnp", "compile", "scratch.capnp", "-oswift"], env = env)

print Path("scratch.swift").open().read()