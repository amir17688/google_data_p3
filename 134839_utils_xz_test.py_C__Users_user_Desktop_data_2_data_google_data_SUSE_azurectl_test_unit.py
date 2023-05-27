
from mock import patch

from test_helper import *
import mock

from azurectl.utils.xz import XZ
from azurectl.azurectl_exceptions import *


class TestXZ:
    def setup(self):
        self.xz = XZ.open('../data/blob.xz')

    def teardown(self):
        self.xz.close()

    def test_read(self):
        assert self.xz.read(128) == 'foo'

    def test_read_already_finished(self):
        self.xz.finished = True
        assert self.xz.read(128) is None

    def test_read_chunks(self):
        with XZ.open('../data/blob.more.xz') as xz:
            chunk = xz.read(8)
            assert chunk == 'Some dat'
            chunk = xz.read(8)
            assert chunk == 'a so tha'
            chunk = xz.read(8)
            assert chunk == 't we can'
            chunk = xz.read(8)
            assert chunk == ' read it'
            chunk = xz.read(8)
            assert chunk == ' as mult'
            chunk = xz.read(8)
            assert chunk == 'iple chu'
            chunk = xz.read(8)
            assert chunk == 'nks'

    def test_uncompressed_size(self):
        assert XZ.uncompressed_size('../data/blob.xz') == 4

    @raises(AzureXZError)
    @patch('subprocess.Popen')
    def test_uncompressed_size_raise(self, mock_popen):
        mock_xz = mock.Mock()
        mock_xz.communicate = mock.Mock(
            return_value=['data', 'error']
        )
        mock_popen.returncode = 1
        mock_popen.return_value = mock_xz
        XZ.uncompressed_size('../data/blob.xz')

    @raises(AssertionError)
    @patch('lzma.LZMADecompressor')
    def test_read_raise(self, mock_xz):
        mock_xz.flush = 'data-which-should-never-be-there'
        with XZ.open('../data/blob.more.xz') as xz:
            chunk = xz.read(8)
