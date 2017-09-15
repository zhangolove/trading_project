import unittest
import sys
sys.path.append("..")
from trading_project.load_data import *

class TestLoadData(unittest.TestCase):

    def test_extract_end_digits(self):
        test_strings = ['20170103', 'abc20170103', '12abc13d20170103']
        for s in test_strings:
            self.assertEqual(extract_end_digits(s), '20170103')

    def test_extract_start_ticker(self):
        test_strings = ['j1', 'j123dfsfs']
        for s in test_strings:
            self.assertEqual(extract_start_ticker(s), 'j')

if __name__ == '__main__':
    unittest.main()