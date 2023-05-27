from sslchecker.lib import SSLCert
import os


TEST_PATH = os.path.dirname(__file__)


class TestSSLCert:
    def test_simple(self):
        with open(os.path.join(TEST_PATH, "google_cert.txt"), "rb") as f:
            d = f.read()
        c1 = SSLCert.from_pem(d)
        assert c1.cn == "google.com"
        assert len(c1.altnames) == 436

        with open(os.path.join(TEST_PATH, "inode_cert.txt"), "rb") as f:
            d = f.read()
        c2 = SSLCert.from_pem(d)
        assert c2.cn == "www.inode.co.nz"
        assert len(c2.altnames) == 2
        assert c2.digest("sha1")
        assert c2.notbefore
        assert c2.notafter
        assert c2.subject
        assert c2.keyinfo == ("RSA", 2048)
        assert c2.serial
        assert c2.issuer
        assert c2.to_pem()
        assert c2.has_expired is not None

        assert not c1 == c2
        assert c1 != c2

    def test_err_broken_sans(self):
        with open(os.path.join(TEST_PATH, "weird_cert.txt"), "rb") as f:
            d = f.read()
        c = SSLCert.from_pem(d)
        # This breaks unless we ignore a decoding error.
        assert c.altnames is not None

    def test_der(self):
        with open(os.path.join(TEST_PATH, "dercert"), "rb") as f:
            d = f.read()
        s = SSLCert.from_der(d)
        assert s.cn
