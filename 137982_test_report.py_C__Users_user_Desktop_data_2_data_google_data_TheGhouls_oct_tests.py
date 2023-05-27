import os
import unittest

from oct.results.report import ReportResults
from oct.results.models import set_database, db

BASE_DIR = os.path.dirname(os.path.realpath(__file__))


class ReportTest(unittest.TestCase):

    def test_empty_results(self):
        """Test report with empty results
        """
        set_database(os.path.join(BASE_DIR, 'fixtures', 'empty_results.sqlite'), db, {})
        report = ReportResults(60, 10)
        report.compile_results()
