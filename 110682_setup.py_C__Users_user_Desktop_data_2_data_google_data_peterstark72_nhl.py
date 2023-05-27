from distutils.core import setup

setup(name='nhl',
      version='4.0',
      py_modules=['nhl'],
      description='Python wrapper for NHL Stats API at nhl.com',
      author='Peter Stark',
      author_email='peterstark72@gmail.com',
      url='https://github.com/peterstark72/nhl',
      requires=['requests'],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: Free for non-commercial use',
          'Natural Language :: English',
          'Operating System :: MacOS :: MacOS X',
          'Programming Language :: Python :: 3.4',
          'Topic :: Utilities'
      ])
