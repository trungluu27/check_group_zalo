"""
Test runner for all unit tests
"""
import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from test_excel_reader import TestExcelReader
from test_excel_writer import TestExcelWriter
from test_comparator import TestComparator


def suite():
    """Create test suite"""
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestExcelReader))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestExcelWriter))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestComparator))
    
    return test_suite


if __name__ == '__main__':
    print("Running Zalo Group Membership Checker Test Suite")
    print("=" * 60)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite())
    
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    
    sys.exit(0 if result.wasSuccessful() else 1)
