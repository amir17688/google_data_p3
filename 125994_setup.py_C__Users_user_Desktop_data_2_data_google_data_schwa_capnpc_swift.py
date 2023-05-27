#from distutils.core import setup
from setuptools import setup, Command

class PyTest(Command):
    user_options = []
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import sys,subprocess
        errno = subprocess.call([sys.executable, "runtests.py"])
        raise SystemExit(errno)

class Coverage(Command):

    # py.test --cov . ; coverage html ; open htmlcov/index.html

    user_options = []
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # TODO: This may be a hack. I dont know!
        import sys,subprocess
        errno = subprocess.call([sys.executable, "runtests.py", "--cov-config=coverage.ini", "--cov", "."])
        if errno:
            raise SystemExit(errno)
        errno = subprocess.call(["coverage", "html", "--rcfile=coverage.ini", "-i"])
        raise SystemExit(errno)


setup(
    name="capnpc_swift",
    version="0.0.1a1",
    packages=["capnpc_swift"],
    url="https://github.com/schwa/capnpc_swift",
    license="BSD License (Simplified)",
    author="Jonathan Wight",
    author_email="jwight@mac.com",
    description="Cap'n Proto plugin for Swift source code generation",
    package_data = {
        "capnpc_swift": [
            "*.capnp",
            "templates/*",
        ],
    },
    install_requires=[
        "click",
        "pycapnp",
        "jinja2",
        "pathlib",
        "addict"
    ],
    entry_points="""
        [console_scripts]
        capnpc-swift=capnpc_swift:cli
        capnpc-passthru=capnpc_swift:passthru
        """,
    zip_safe=False,
    cmdclass = {"test": PyTest, "coverage": Coverage},
    # https://pypi.python.org/pypi?:action=list_classifiers
    classifiers = [
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Swift",
    ],
)
