#!/usr/bin/env python
from graphitepager import __version__
import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def open_file(fname):
    return open(os.path.join(os.path.dirname(__file__), fname))


def run_setup():
    setup(
        name='graphitepager',
        version=__version__,
        author='Philip Cristiano',
        author_email='philipcristiano@gmail.com',
        packages=['graphitepager', 'graphitepager.notifiers'],
        url='http://github.com/philipcristiano/graphite-pager',
        license='BSD',
        classifiers=[
            'Intended Audience :: System Administrators',
            'License :: OSI Approved :: BSD License',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 2.6',
            'Topic :: System :: Monitoring',
        ],
        description='',
        keywords='',
        test_suite='tests',
        long_description=open_file('README.rst').read(),
        install_requires=open_file('requirements.txt').readlines(),
        zip_safe=True,
        entry_points="""
        [console_scripts]
        graphite-pager=graphitepager.worker:main
        """,
    )

if __name__ == '__main__':
    run_setup()
