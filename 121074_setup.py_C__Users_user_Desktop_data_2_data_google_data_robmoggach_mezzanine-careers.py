from setuptools import setup, find_packages
import sys, os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import careers

setup(
    name='mezzanine-careers',
    version=careers.__version__,
    url='https://github.com/mogga/mezzanine-careers',
    author='Robert Moggach',
    author_email='rob@moggach.tv',
    license='BSD',
    description='Job Posting application for the Mezzanine CMS',
    long_description=open('README.rst').read(),
    keywords='django, mezzanine, careers',
    packages=find_packages(),
    setup_requires=('setuptools'),
    install_requires=('setuptools', 'mezzanine'),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',],
    zip_safe=False,
    include_package_data=True,
)
