"""
Unit tests for Excel Writer module
"""
import unittest
from pathlib import Path
import pandas as pd
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from excel.writer import ExcelWriter


class TestExcelWriter(unittest.TestCase):
    """Test cases for ExcelWriter class"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_output = Path('test_output.xlsx')
        self.missing_users = [
            {'phone': '0901', 'name': 'User1'},
            {'phone': '0902', 'name': 'User2'},
            {'phone': '0903', 'name': 'User3'}
        ]

    def tearDown(self):
        """Clean up test files"""
        if self.test_output.exists():
            self.test_output.unlink()

    def test_write_results_xlsx(self):
        """Test writing results to XLSX with both report sheets"""
        writer = ExcelWriter(str(self.test_output), format='xlsx')
        extra = ['GroupOnly1', 'GroupOnly2']
        result = writer.write_results(self.missing_users, extra_in_group=extra)
        self.assertTrue(result)
        self.assertTrue(self.test_output.exists())

        # Verify missing sheet content
        missing_df = pd.read_excel(self.test_output, sheet_name='Missing Members')
        self.assertEqual(len(missing_df), 3)
        self.assertIn('User1', missing_df['Tên Zalo'].values)
        self.assertIn('0901', missing_df['SĐT Zalo'].astype(str).values)

        # Verify extra sheet content
        extra_df = pd.read_excel(self.test_output, sheet_name='In Group Not In Excel')
        self.assertEqual(len(extra_df), 2)
        self.assertIn('GroupOnly1', extra_df['Tên Zalo'].values)
        self.assertEqual(list(extra_df.columns), ['Tên Zalo'])

    def test_write_results_csv(self):
        """Test writing results to CSV (primary report only)"""
        csv_output = Path('test_output.csv')
        writer = ExcelWriter(str(csv_output), format='csv')
        result = writer.write_results(self.missing_users)
        self.assertTrue(result)
        self.assertTrue(csv_output.exists())

        # Clean up
        if csv_output.exists():
            csv_output.unlink()

    def test_write_with_metadata(self):
        """Test writing with metadata"""
        metadata = {
            'group_url': 'https://test.com/group',
            'total': 10
        }
        writer = ExcelWriter(str(self.test_output), format='xlsx')
        result = writer.write_results(self.missing_users, metadata)
        self.assertTrue(result)

        # Verify metadata sheet exists
        excel_file = pd.ExcelFile(self.test_output)
        self.assertIn('Metadata', excel_file.sheet_names)

    def test_write_comparison_report(self):
        """Test writing comparison report"""
        found = ['User4', 'User5']
        missing = [{'phone': '0901', 'name': 'User1'}, {'phone': '0902', 'name': 'User2'}]
        extra = ['GroupOnly1']
        writer = ExcelWriter(str(self.test_output), format='xlsx')

        result = writer.write_comparison_report(
            found, missing,
            'https://test.com/group',
            'test.xlsx',
            extra_in_group=extra
        )
        self.assertTrue(result)
        self.assertTrue(self.test_output.exists())

    def test_invalid_format(self):
        """Test handling of invalid format"""
        writer = ExcelWriter('test.txt', format='invalid')
        with self.assertRaises(ValueError):
            writer.write_results(self.missing_users)


if __name__ == '__main__':
    unittest.main()
