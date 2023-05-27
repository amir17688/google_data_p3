
from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

setup(
	name = 'emogenerator',
	version = '0.1.14',
	author = 'Jonathan Wight',
	author_email = 'jwight@mac.com',
	description = 'Estranged Managed Object Generator',
	long_description = file('README.txt').read(),
	license = 'BSD License',
	platform = 'Mac OS X',
	url = 'http://github.com/schwa/emogenerator',
	classifiers = [
		'Development Status :: 3 - Alpha',
		'Environment :: MacOS X :: Cocoa',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: BSD License',
		'Operating System :: MacOS :: MacOS X',
		'Programming Language :: Objective C',
		'Topic :: Database',
		'Topic :: Software Development :: Build Tools',
		],

	include_package_data = True,
	install_requires = ['genshi >= 0.5'],
	packages = find_packages(),
	package_data = { '': ['templates/*'] },
	scripts = ['scripts/emogenerator'],
	)

