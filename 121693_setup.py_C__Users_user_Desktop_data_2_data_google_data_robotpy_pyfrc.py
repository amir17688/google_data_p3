#!/usr/bin/env python3

import sys
if sys.version_info[0] < 3:
    sys.stderr.write("ERROR: pyfrc requires python 3!")
    exit(1)

from os.path import dirname, exists, join
import subprocess
from setuptools import find_packages, setup
from urllib.request import urlretrieve

setup_dir = dirname(__file__)
git_dir = join(setup_dir, '.git')
base_package = 'pyfrc'
version_file = join(setup_dir, 'lib', base_package, 'version.py')

# Download plink/psftp
ext_dir = join(setup_dir, 'lib', base_package, 'robotpy', 'win32')
ext_files = {
    'plink.exe': 'http://the.earth.li/~sgtatham/putty/latest/x86/plink.exe',
    'psftp.exe': 'http://the.earth.li/~sgtatham/putty/latest/x86/psftp.exe'
}

for file, uri in ext_files.items():
    if exists(join(ext_dir, file)):
        continue
    
    print("Downloading %s" % file)
    def _reporthook(count, blocksize, totalsize):
        percent = int(count*blocksize*100/totalsize)
        sys.stdout.write("\r%02d%%" % percent)
        sys.stdout.flush()

    urlretrieve(uri, join(ext_dir, file), _reporthook)
    print()

# Automatically generate a version.py based on the git version
if exists(git_dir):
    p = subprocess.Popen(["git", "describe", "--tags", "--long", "--dirty=-dirty"],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    # Make sure the git version has at least one tag
    if err:
        print("Error: You need to create a tag for this repo to use the builder")
        sys.exit(1)

    # Convert git version to PEP440 compliant version
    # - Older versions of pip choke on local identifiers, so we can't include the git commit
    v, commits, local = out.decode('utf-8').rstrip().split('-', 2)
    if commits != '0' or '-dirty' in local:
        v = '%s.post0.dev%s' % (v, commits)

    # Create the version.py file
    with open(version_file, 'w') as fp:
        fp.write("# Autogenerated by setup.py\n__version__ = '{0}'".format(v))

if exists(version_file):
    with open(version_file, 'r') as fp:
        exec(fp.read(), globals())
else:
    __version__ = "master"

with open(join(setup_dir, 'requirements.txt')) as requirements_file:
    install_requires = requirements_file.readlines()

with open(join(dirname(__file__), 'README.md'), 'r') as readme_file:
    long_description = readme_file.read()

setup(name='pyfrc',
      version=__version__,
      description='Development tools library for python interpreter used for the FIRST Robotics Competition',
      long_description=long_description,
      author='Dustin Spicuzza, Sam Rosenblum',
      author_email='robotpy@googlegroups.com',
      url='https://github.com/robotpy/pyfrc',
      license='BSD',
      packages=find_packages(where='lib'),
      package_dir={'': 'lib'},
      package_data={'pyfrc': ['robotpy/win32/plink.exe',
                              'robotpy/win32/psftp.exe']},
      install_requires=install_requires,
      classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development'
        ],
      entry_points={'robotpy': [
        'add-tests = pyfrc.mains.cli_add_tests:PyFrcAddTests',
        'coverage = pyfrc.mains.cli_coverage:PyFrcCoverage',
        'deploy = pyfrc.mains.cli_deploy:PyFrcDeploy',
        'profiler = pyfrc.mains.cli_profiler:PyFrcProfiler',
        'sim = pyfrc.mains.cli_sim:PyFrcSim',
        'test = pyfrc.mains.cli_test:PyFrcTest'
      ]}
)


