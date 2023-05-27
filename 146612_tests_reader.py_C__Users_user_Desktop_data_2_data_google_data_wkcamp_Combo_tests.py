import unittest
import os

from combo.reader import Reader

class TestReader(unittest.TestCase):
    def setUp(self):
        # Faked freeze information
        self.freeze_output = "package==4.2"
        # Create Combofile (assuming that it exists) 
        combofile = open("./Combofile", "a+")
        combofile.write("package:4.2\n")
        combofile.close()
        # Create Reader object to read this combofile
        self.reader = Reader()
        self.expected_match = [("package", "4.2")]

    def test_combofile_pkgs_match(self):
        pkgs_match = self.reader.combofile_pkgs()
        self.assertListEqual(pkgs_match, self.expected_match)

    # This will take care of read_pip_freeze as well
    def test_filter_freeze(self): 
        filtered_freeze = self.reader.filter_freeze(self.freeze_output) 
        self.assertListEqual(filtered_freeze, self.expected_match)

    #TODO: find way to test unlisted() and removed() 
    def tearDown(self):
        # Remove that Combofile (Note: this will not scale if unit tests grow)
        os.remove("./Combofile") 

if __name__ == "__main__":
    unittest.main()
