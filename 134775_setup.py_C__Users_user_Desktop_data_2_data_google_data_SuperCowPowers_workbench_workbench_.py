#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
from setuptools import setup


readme = open('workbench_cli/README.rst').read()
long_description = readme
doclink = '''
Documentation
-------------

The full documentation is at http://workbench.rtfd.org. '''

exec(open('workbench_cli/version.py').read())
setup(
    name='workbench_cli',
    version=__version__,
    description='Command Line Interface for Workbench',
    long_description=readme + '\n\n' + doclink + '\n\n',
    author='The Workbench Team',
    author_email='support@supercowpowers.com',
    url='http://github.com/SuperCowPowers/workbench',
    packages=['workbench_cli'],
    package_dir={'workbench_cli': 'workbench_cli'},
    include_package_data=True,
    scripts=['workbench_cli/workbench'],
    install_requires=['funcsigs', 'ipython', 'lz4', 
                      'pandas', 'pytest', 'zerorpc'],
    license='MIT',
    zip_safe=False,
    keywords='workbench security python',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
    ]
)
