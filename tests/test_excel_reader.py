"""
Unit tests for Excel Reader module
"""
import unittest
import pandas as pd
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from excel.reader import ExcelReader


class TestExcelReader(unittest.TestCase):
    """Test cases for ExcelReader class"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_file = Path('test_temp.xlsx')

    def tearDown(self):
        """Clean up test files"""
        if self.test_file.exists():
            self.test_file.unlink()
        test_file2 = Path('test_temp2.xlsx')
        if test_file2.exists():
            test_file2.unlink()

    def test_read_file_xlsx(self):
        """Test reading .xlsx file"""
        test_data = {
            'SĐT': ['0901', '0902', '0903'],
            'Tên': ['User1', 'User2', 'User3']
        }
        pd.DataFrame(test_data).to_excel(self.test_file, index=False, engine='openpyxl')

        reader = ExcelReader(str(self.test_file))
        df = reader.read_file()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 3)

    def test_get_usernames_with_sdt_ten(self):
        """Test extracting names with Vietnamese headers SĐT + Tên"""
        test_data = {
            'SĐT': ['0901', '0902', '0903'],
            'Tên': ['User1', 'User2', 'User3']
        }
        pd.DataFrame(test_data).to_excel(self.test_file, index=False, engine='openpyxl')

        reader = ExcelReader(str(self.test_file))
        usernames = reader.get_usernames()
        self.assertEqual(len(usernames), 3)
        self.assertIn('User1', usernames)
        self.assertIn('User2', usernames)
        self.assertIn('User3', usernames)

    def test_auto_detect_case_and_accent_insensitive(self):
        """Test case-insensitive and accent-insensitive detection for required columns"""
        test_data = {
            'sDt ZaLo': ['0901', '0902', '0903'],
            'TeN ZaLo': ['Alice', 'Bob', 'Charlie']
        }
        test_file2 = Path('test_temp2.xlsx')
        pd.DataFrame(test_data).to_excel(test_file2, index=False, engine='openpyxl')

        reader = ExcelReader(str(test_file2))
        usernames = reader.get_usernames()
        self.assertEqual(len(usernames), 3)
        self.assertIn('Alice', usernames)
        self.assertIn('Bob', usernames)
        self.assertIn('Charlie', usernames)

    def test_require_both_phone_and_name_columns(self):
        """Test that both required columns are mandatory"""
        test_data = {
            'Tên': ['Alice', 'Bob'],
            'Email': ['a@test.com', 'b@test.com']
        }
        test_file2 = Path('test_temp2.xlsx')
        pd.DataFrame(test_data).to_excel(test_file2, index=False, engine='openpyxl')

        reader = ExcelReader(str(test_file2))
        with self.assertRaises(ValueError):
            reader.get_usernames()

    def test_invalid_file_format(self):
        """Test handling of invalid file format"""
        with self.assertRaises(ValueError):
            reader = ExcelReader('test.txt')
            reader.read_file()

    def test_missing_file(self):
        """Test handling of missing file"""
        with self.assertRaises(Exception):
            reader = ExcelReader('nonexistent.xlsx')
            reader.read_file()


if __name__ == '__main__':
    unittest.main()
