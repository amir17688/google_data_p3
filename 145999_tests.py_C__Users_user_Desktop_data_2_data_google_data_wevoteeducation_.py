# import_export_theunitedstatesio/tests.py
# Brought to you by We Vote. Be good.
# -*- coding: UTF-8 -*-

from django.test import TestCase
import csv

from import_export_theunitedstatesio.models import TheUnitedStatesIoLegislatorCurrent, LEGISLATORS_CURRENT_CSV_FILE


# Create your tests here.
class ImportExportTheUnitedStatesIoTests(TestCase):

    def test_csv_file_can_be_found_in_legislators_current(self):
        """
        Is there a version of the legislators_current data?
        """

    def test_csv_file_headers_match_what_is_expected_in_legislators_current(self):
        """
        Do the headers in the legislators_current csv file
        """
        # "last_name",              # row[0]
        # "first_name",             # row[1]
        # "birthday",               # row[2]
        # "gender",                 # row[3]
        # "type",                   # row[4]
        # "state",                  # row[5]
        # "district",               # row[6]
        # "party",                  # row[7]
        # "url",                    # row[8]
        # "address",                # row[9]
        # "phone",                  # row[10]
        # "contact_form",           # row[11]
        # "rss_url",                # row[12]
        # "twitter",                # row[13]
        # "facebook",               # row[14]
        # "facebook_id",            # row[15]
        # "youtube",                # row[16]
        # "youtube_id",             # row[17]
        # "bioguide_id",            # row[18]
        # "thomas_id",              # row[19]
        # "opensecrets_id",         # row[20]
        # "lis_id",                 # row[21]
        # "cspan_id",               # row[22]
        # "govtrack_id",            # row[23]
        # "votesmart_id",           # row[24]
        # "ballotpedia_id",         # row[25]
        # "washington_post_id",     # row[26]
        # "icpsr_id",               # row[27]
        # "wikipedia_id"            # row[28]
        with open(LEGISLATORS_CURRENT_CSV_FILE, 'rU') as legislators_current_data:
            reader = csv.reader(legislators_current_data)   # Create a regular tuple reader
            for index, legislator_row in enumerate(reader):
                # print "import_legislators_current_csv: " + legislator_row[0] # For debugging
                self.assertEqual(legislator_row[0] == "last_name", True)
                self.assertEqual(legislator_row[1] == "first_name", True)
                self.assertEqual(legislator_row[2] == "birthday", True)
                self.assertEqual(legislator_row[3] == "gender", True)
                self.assertEqual(legislator_row[4] == "type", True)
                self.assertEqual(legislator_row[5] == "state", True)
                self.assertEqual(legislator_row[6] == "district", True)
                self.assertEqual(legislator_row[7] == "party", True)
                self.assertEqual(legislator_row[8] == "url", True)
                self.assertEqual(legislator_row[9] == "address", True)
                self.assertEqual(legislator_row[10] == "phone", True)
                self.assertEqual(legislator_row[11] == "contact_form", True)
                self.assertEqual(legislator_row[12] == "rss_url", True)
                self.assertEqual(legislator_row[13] == "twitter", True)
                self.assertEqual(legislator_row[14] == "facebook", True)
                self.assertEqual(legislator_row[15] == "facebook_id", True)
                self.assertEqual(legislator_row[16] == "youtube", True)
                self.assertEqual(legislator_row[17] == "youtube_id", True)
                self.assertEqual(legislator_row[18] == "bioguide_id", True)
                self.assertEqual(legislator_row[19] == "thomas_id", True)
                self.assertEqual(legislator_row[20] == "opensecrets_id", True)
                self.assertEqual(legislator_row[21] == "lis_id", True)
                self.assertEqual(legislator_row[22] == "cspan_id", True)
                self.assertEqual(legislator_row[23] == "govtrack_id", True)
                self.assertEqual(legislator_row[24] == "votesmart_id", True)
                self.assertEqual(legislator_row[25] == "ballotpedia_id", True)
                self.assertEqual(legislator_row[26] == "washington_post_id", True)
                self.assertEqual(legislator_row[27] == "icpsr_id", True)
                self.assertEqual(legislator_row[28] == "wikipedia_id", True)
                break

    def test_csv_file_header_index_error_in_legislators_current(self):
        try:
            with open(LEGISLATORS_CURRENT_CSV_FILE, 'rU') as legislators_current_data:
                reader = csv.reader(legislators_current_data)   # Create a regular tuple reader
                for index, legislator_row in enumerate(reader):
                    print legislator_row[29]
                    self.fail('There is a value in the array after the last expected item.')
                    break
        except IndexError:
            pass