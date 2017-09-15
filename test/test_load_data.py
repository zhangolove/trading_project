import unittest
import sys
sys.path.append("..")
from trading_project.load_data import *

class TestLoadData(unittest.TestCase):
    def setUp(self):
        self.begin_time = '20170103'
        self.end_time = '20170105'
        self.tick = 'cu'
        self.path = '../data/marketdatacsv'

    def test_extract_end_digits(self):
        test_strings = ['20170103', 'abc20170103', '12abc13d20170103']
        for s in test_strings:
            self.assertEqual(extract_end_digits(s), '20170103')

    def test_extract_start_ticker(self):
        test_strings = ['j1', 'j123dfsfs']
        for s in test_strings:
            self.assertEqual(extract_start_ticker(s), 'j')

    def test_try_parsing_date(self):
        date = '20170103 08:59:00 500'
        time = try_parsing_date(date)
        self.assertEqual(time.hour, 8)

    def test_number_of_unfiltered_loaded_data(self):
        begin_time, end_time = parse_user_provided_time(self.begin_time, self.end_time)
        folders = get_folders_of_time_ranges(self.path, begin_time, end_time)
        contract, selected_files = select_most_active_contract(self.tick, folders)
        for sf in selected_files:
            expected_lines = 0
            with open(sf) as f:
                expected_lines = sum(1 for line in f)
            self.assertEqual(expected_lines, csv_2_df(sf).shape[0])

    def test_filtered_loaded_data(self):
        begin_time, end_time = parse_user_provided_time(self.begin_time, self.end_time)
        folders = get_folders_of_time_ranges(self.path, begin_time, end_time)
        contract, selected_files = select_most_active_contract(self.tick, folders)
        for sf in selected_files:
            raw = csv_2_df(sf)
            filtered = load_file_data(sf, begin_time, end_time)
            ds1 = set([ tuple(line) for line in raw.values.tolist()])
            ds2 = set([ tuple(line) for line in filtered.values.tolist()])
            for t in ds1.difference(ds2):
                date_string = '{} {} {}'.format(t[0], t[1], t[2])
                time = try_parsing_date(date_string)
                self.assertTrue(time >= begin_time)
                self.assertTrue(time <= end_time)
                self.assertTrue(time.hour < 9)

if __name__ == '__main__':
    unittest.main()