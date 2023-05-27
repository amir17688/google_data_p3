from setuptools import setup, find_packages

setup(
	name = 'cifilter',
	version = '0.4.2',
	author = 'Jonathan Wight',
	author_email = 'jwight@mac.com',
	description = 'CoreImage command line tool',
	long_description = file('README.txt').read(),
	license = 'BSD License',
	platforms = 'Mac OS X',
	url = 'http://github.com/schwa/cifilter/',
	classifiers = [
		'Development Status :: 3 - Alpha',
		'Environment :: MacOS X :: Cocoa',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: BSD License',
		'Operating System :: MacOS :: MacOS X',
		'Programming Language :: Objective C',
		'Topic :: Multimedia :: Graphics',
		'Topic :: Multimedia :: Graphics :: Editors :: Raster-Based',
		'Topic :: Software Development',
		],

	packages = find_packages(),
	scripts = ['scripts/cifilter'],
	)

