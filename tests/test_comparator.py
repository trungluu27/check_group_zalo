"""
Unit tests for Comparator module
"""
import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.comparator import Comparator


class TestComparator(unittest.TestCase):
    """Test cases for Comparator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.comparator = Comparator(threshold=0.85, case_sensitive=False)
        self.excel_names = ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Wonder']
        self.group_members = {'john doe', 'Jane Smith', 'robert johnson', 'Charlie Brown'}
    
    def test_normalize_name(self):
        """Test name normalization"""
        name = "  John   Doe  "
        normalized = self.comparator.normalize_name(name)
        self.assertEqual(normalized, "john doe")
    
    def test_exact_match(self):
        """Test exact matching"""
        found, missing = self.comparator.exact_match(self.excel_names, self.group_members)
        self.assertIn('John Doe', found)  # Should match 'john doe'
        self.assertIn('Jane Smith', found)  # Exact match
        self.assertIn('Bob Johnson', missing)  # Different from 'robert johnson'
        self.assertIn('Alice Wonder', missing)  # Not in group
    
    def test_fuzzy_match(self):
        """Test fuzzy matching"""
        found, missing, details = self.comparator.fuzzy_match(self.excel_names, self.group_members)
        self.assertIn('John Doe', found)
        self.assertIn('Jane Smith', found)
        # Bob Johnson might match Robert Johnson with fuzzy matching
        self.assertIn('Alice Wonder', missing)
    
    def test_compare_exact(self):
        """Test compare with exact matching"""
        results = self.comparator.compare(self.excel_names, self.group_members, use_fuzzy=False)
        self.assertEqual(results['total_excel'], 4)
        self.assertEqual(results['total_group'], 4)
        self.assertEqual(results['method'], 'exact')
        self.assertGreater(len(results['found']), 0)
    
    def test_compare_fuzzy(self):
        """Test compare with fuzzy matching"""
        results = self.comparator.compare(self.excel_names, self.group_members, use_fuzzy=True)
        self.assertEqual(results['total_excel'], 4)
        self.assertEqual(results['total_group'], 4)
        self.assertEqual(results['method'], 'fuzzy')
        self.assertGreater(len(results['found']), 0)
    
    def test_case_insensitive(self):
        """Test case insensitive comparison"""
        comparator = Comparator(case_sensitive=False)
        excel = ['JOHN DOE', 'jane smith']
        group = {'john doe', 'JANE SMITH'}
        found, missing = comparator.exact_match(excel, group)
        self.assertEqual(len(found), 2)
        self.assertEqual(len(missing), 0)
    
    def test_empty_lists(self):
        """Test with empty lists"""
        results = self.comparator.compare([], set(), use_fuzzy=True)
        self.assertEqual(results['total_excel'], 0)
        self.assertEqual(results['total_group'], 0)
        self.assertEqual(len(results['found']), 0)
        self.assertEqual(len(results['missing']), 0)


if __name__ == '__main__':
    unittest.main()
