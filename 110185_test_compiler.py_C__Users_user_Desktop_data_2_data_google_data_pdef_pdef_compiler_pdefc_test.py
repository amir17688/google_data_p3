# encoding: utf-8
import os
import unittest
import pdefc


class TestCompiler(unittest.TestCase):
    def filepath(self):
        return os.path.join(os.path.dirname(__file__), 'test.pdef')
    
    def test_compile__should_compile_package(self):
        path = self.filepath()
        package = pdefc.compile(path)
        assert package
        assert len(package.files) == 1
    
    def test_compile__should_compile_files(self):
        path = self.filepath()
        package = pdefc.compile(path)
        
        file = package.files[0]
        assert file.dotname == 'test'
        assert file.path == 'test.pdef'
        assert len(file.types) == 5
