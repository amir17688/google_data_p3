from ez_setup import use_setuptools
use_setuptools()  # nopep8

from setuptools import setup, find_packages

setup(
    name='activitysim',
    version='0.1dev',
    description='Activity-Based Travel Modeling',
    author='contributing authors',
    author_email='',
    license='BSD-3',
    url='https://github.com/udst/activitysim',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 2.7',
        'License :: OSI Approved :: BSD 3-Clause License'
    ],
    packages=find_packages(exclude=['*.tests']),
    install_requires=[
        'numpy >= 1.8.0',
        'openmatrix >= 0.2.2',
        'orca >= 1.1',
        'pandas >= 0.18.0',
        'pyyaml >= 3.0',
        'tables >= 3.1.0',
        'toolz >= 0.7',
        'zbox >= 1.2',
        'psutil >= 4.1'
    ]
)
