# encoding: utf-8
import unittest
from mock import Mock
from pdefc import cli


class TestCli(unittest.TestCase):
    def setUp(self):
        self.compiler = Mock()
        
    def test_version(self):
        cli.main(['version'], self.compiler)
        self.compiler.version.assert_called_once_with()
    
    def test_check(self):
        args = ['check', 'file/path.pdef']
        cli.main(args, self.compiler)
        
        self.compiler.compile.assert_called_once_with('file/path.pdef')
    
    def test_gen_java(self):
        args = ['gen-java', 'src/path.pdef', '--dst', 'dst/path', '--package', 'java.package']
        cli.main(args, self.compiler)
        
        self.compiler.generate_java.assert_called_once_with(
            'src/path.pdef', 'dst/path', jpackage_name='java.package')
    
    def test_gen_objc(self):
        args = ['gen-objc', 'src/path.pdef', '--dst', 'dst/path', '--prefix', 'NS']
        cli.main(args, self.compiler)
        
        self.compiler.generate_objc.assert_called_once_with(
            'src/path.pdef', 'dst/path', prefix='NS')
