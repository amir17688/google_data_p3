# encoding: utf-8

# Copyright: 2013-2014 Ivan Korobkov <ivan.korobkov@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import io
import os

from pdefc.cli import main
from pdefc.version import __version__
from pdefc import lang, parser, java, objc

__title__ = 'pdef-compiler'
__author__ = 'Ivan Korobkov <ivan.korobkov@gmail.com>'
__license__ = 'Apache License 2.0'
__copyright__ = 'Copyright 2013-2014 Ivan Korobkov'
FILE_EXT = '.pdef'


class CompilerException(Exception):
    def __init__(self, message, errors=None):
        super(CompilerException, self).__init__(message)
        self.errors = errors


def version():
    return __version__


def compile(path):
    '''Compile a package from a path.'''
    package = _parse(path)
    errors = package.compile()
    if errors:
        raise CompilerException('Compiler errors', errors)

    return package


def generate_java(src, out, jpackage_name=None):
    '''Generates java files.'''
    package = compile(src)
    java.generate(package, out, jpackage_name=jpackage_name)


def generate_objc(src, out, prefix=None):
    '''Generates objective-c files.'''
    package = compile(src)
    objc.generate(package, out, prefix=prefix)


def _parse(path):
    '''Parse a package from a path.'''
    parse = parser.Parser()
    errors = lang.Errors()
    package = lang.Package()

    for fullpath, relpath in _walk(path):
        source = _read(fullpath)
        file, file_errors = parse.parse(source, relpath)

        if file_errors:
            errors.add_errors(file_errors)
        else:
            package.add_file(file)

    if errors:
        raise CompilerException('Syntax errors', errors)
    return package


def _walk(rootpath):
    '''Yield (fullpath, relpath).'''
    if os.path.isfile(rootpath):
        relpath = os.path.split(rootpath)[1]
        yield rootpath, relpath

    elif os.path.isdir(rootpath):
        for root, dirs, files in os.walk(rootpath):
            for filename in files:
                if not filename.lower().endswith(FILE_EXT):
                    continue

                fullpath = os.path.join(root, filename)
                relpath = os.path.relpath(fullpath, rootpath)
                yield fullpath, relpath

    else:
        raise CompilerException('File or directory does not exist "%s"' % rootpath)


def _read(path):
    '''Read a file, parse it and return (file, errors).'''
    with io.open(path, 'rt', encoding='utf-8') as f:
        return f.read()
