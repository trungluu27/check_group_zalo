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
        found, missing, _matched = self.comparator.exact_match(self.excel_names, self.group_members)
        self.assertIn('John Doe', found)  # Should match 'john doe'
        self.assertIn('Jane Smith', found)  # Exact match
        self.assertIn('Bob Johnson', missing)  # Different from 'robert johnson'
        self.assertIn('Alice Wonder', missing)  # Not in group
    
    def test_fuzzy_match(self):
        """Test fuzzy matching"""
        found, missing, details, _matched = self.comparator.fuzzy_match(self.excel_names, self.group_members)
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
        found, missing, _matched = comparator.exact_match(excel, group)
        self.assertEqual(len(found), 2)
        self.assertEqual(len(missing), 0)
    
    def test_empty_lists(self):
        """Test with empty lists"""
        results = self.comparator.compare([], set(), use_fuzzy=True)
        self.assertEqual(results['total_excel'], 0)
        self.assertEqual(results['total_group'], 0)
        self.assertEqual(len(results['found']), 0)
        self.assertEqual(len(results['missing']), 0)


class TestVietnameseToneMarks(unittest.TestCase):
    """
    Vietnamese allows the tone mark to sit on either vowel of a syllable
    ("Thùy" vs "Thuỳ"). Both spellings must be treated as the same person.
    """

    # (old-style placement, new-style placement)
    EQUIVALENT_SPELLINGS = [
        ('Thùy Dương', 'Thuỳ Dương'),
        ('Hòa', 'Hoà'),
        ('Thúy', 'Thuý'),
        ('Khỏe', 'Khoẻ'),
        ('Tòa', 'Toà'),
        ('Hủy', 'Huỷ'),
        ('Nguyễn Thị Hòa', 'Nguyễn Thị Hoà'),
        ('Lê Thị Thúy Hằng', 'Lê Thị Thuý Hằng'),
    ]

    def setUp(self):
        self.comparator = Comparator(threshold=0.85, case_sensitive=False)

    def test_placement_variants_normalize_identically(self):
        """Both tone-mark conventions collapse to the same normalized form"""
        for old_style, new_style in self.EQUIVALENT_SPELLINGS:
            with self.subTest(pair=(old_style, new_style)):
                self.assertEqual(
                    self.comparator.normalize_name(old_style),
                    self.comparator.normalize_name(new_style),
                )

    def test_placement_variants_match_exactly(self):
        """The pair is found by exact matching, without relying on fuzzy"""
        for old_style, new_style in self.EQUIVALENT_SPELLINGS:
            with self.subTest(pair=(old_style, new_style)):
                found, missing, _matched = self.comparator.exact_match(
                    [old_style], {new_style}
                )
                self.assertEqual(found, [old_style])
                self.assertEqual(missing, [])

    def test_placement_variants_match_fuzzily(self):
        """The reported case: 'Thùy Dương' vs 'Thuỳ Dương' at threshold 0.85"""
        found, missing, _details, _matched = self.comparator.fuzzy_match(
            ['Thùy Dương'], {'Thuỳ Dương'}
        )
        self.assertEqual(found, ['Thùy Dương'])
        self.assertEqual(missing, [])

    def test_different_tones_stay_distinct(self):
        """Folding must not merge names that differ by the tone itself"""
        distinct_pairs = [
            ('Mà', 'Má'),      # huyền vs sắc
            ('Thùy', 'Thúy'),  # huyền vs sắc
            ('Hỏa', 'Hòa'),    # hỏi vs huyền
            ('Bạn', 'Bàn'),    # nặng vs huyền
        ]
        for left, right in distinct_pairs:
            with self.subTest(pair=(left, right)):
                self.assertNotEqual(
                    self.comparator.normalize_name(left),
                    self.comparator.normalize_name(right),
                )

    def test_letter_order_preserved(self):
        """Only tone marks move — base letters keep their order"""
        distinct_pairs = [
            ('an', 'na'),
            ('Lào', 'Loà'),    # same tone, different letter order
            ('Bắc', 'Cắb'),
        ]
        for left, right in distinct_pairs:
            with self.subTest(pair=(left, right)):
                self.assertNotEqual(
                    self.comparator.normalize_name(left),
                    self.comparator.normalize_name(right),
                )

    def test_letter_shaping_marks_preserved(self):
        """Breve / circumflex / horn are part of the letter, not the tone"""
        distinct_pairs = [
            ('Dương', 'Duong'),  # horn
            ('Hằng', 'Hang'),    # breve + tone
            ('Tuấn', 'Tuan'),    # circumflex + tone
            ('Ăn', 'An'),        # breve
        ]
        for left, right in distinct_pairs:
            with self.subTest(pair=(left, right)):
                self.assertNotEqual(
                    self.comparator.normalize_name(left),
                    self.comparator.normalize_name(right),
                )

    def test_ascii_names_unaffected(self):
        """Folding is a no-op for names without Vietnamese diacritics"""
        self.assertEqual(self.comparator.normalize_name('  John   Doe '), 'john doe')
        self.assertNotEqual(
            self.comparator.normalize_name('John Doe'),
            self.comparator.normalize_name('Jane Doe'),
        )

    def test_different_tones_do_not_fuzzy_match(self):
        """
        Regression: fuzzywuzzy's default force_ascii=True deleted Latin-1
        accents ('ù' -> gone) but kept Vietnamese-only ones ('ủ' -> kept),
        so "Thùy" and "Thúy" both folded to "thy" and scored 100 — reporting
        someone as present in a group when they were not.
        """
        distinct_names = [
            ('Thùy', 'Thúy'),
            ('Thủy', 'Thụy'),
            ('Lê Hoàng', 'Lê Hương'),
        ]
        for excel_name, group_name in distinct_names:
            with self.subTest(pair=(excel_name, group_name)):
                found, missing, _details, _matched = self.comparator.fuzzy_match(
                    [excel_name], {group_name}
                )
                self.assertEqual(found, [], f"{excel_name!r} wrongly matched {group_name!r}")
                self.assertEqual(missing, [excel_name])

    def test_normalization_is_idempotent(self):
        """Normalizing an already-normalized name changes nothing"""
        for old_style, _ in self.EQUIVALENT_SPELLINGS:
            with self.subTest(name=old_style):
                once = self.comparator.normalize_name(old_style)
                self.assertEqual(once, self.comparator.normalize_name(once))


if __name__ == '__main__':
    unittest.main()
