#! /usr/bin/env python
from setuptools import setup, find_packages
from io import open
import versioneer

setup(
    name='flask_basic_roles',
    packages=find_packages(exclude=["tests"]),
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='A plugin for adding very simple users + roles to a '
                'flask app',
    author='Dillon Dixon',
    author_email='dillondixon@gmail.com',
    url='https://github.com/ownaginatious/flask-basic-roles',
    license='MIT',
    keywords=['flask', 'python', 'authentication', 'authorization'],
    classifiers=[
        'Framework :: Flask',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5'
    ],
    install_requires=[line.strip()
                      for line in open("requirements.txt", "r",
                                       encoding="utf-8").readlines()],
)
