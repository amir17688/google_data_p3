__author__ = 'schwa'

__all__ = ['schema']

import capnp
from pathlib import Path
import tempfile

temp_dir = Path(tempfile.mkdtemp())

# TODO: Provide a mechanism for user override this
capnp_schema_path = Path("/usr/local/include/capnp/schema.capnp")
if not capnp_schema_path.exists():
    raise Exception("No schema found")

# py-capnp doesn't like the "using cxx" namespace lines so we strip them out into a temp file.
# TODO: File bug with py-capnp: https://github.com/jparyani/pycapnp
lines = capnp_schema_path.open().readlines()
skip_lines = ['using Cxx = import "/capnp/c++.capnp";\n',
              '$Cxx.namespace("capnp::schema");\n']
lines = (line for line in lines if line not in skip_lines)

capnp_schema_path = temp_dir / capnp_schema_path.name

capnp_schema_path.open('w').writelines(lines)
assert capnp_schema_path.exists()

capnp.remove_import_hook()
schema = capnp.load(str(capnp_schema_path))
