from typing import List, Set, Tuple, Dict
from fuzzywuzzy import fuzz
import re
import unicodedata

# The five Vietnamese tone marks as combining characters (i.e. after NFD).
# Letter-shaping marks are deliberately NOT here — breve (ă), circumflex
# (â/ê/ô) and horn (ơ/ư) belong to the letter itself, not to the tone, so
# moving them would merge genuinely different letters.
_TONE_MARKS = frozenset(
    '̀'  # huyền
    '́'  # sắc
    '̃'  # ngã
    '̉'  # hỏi
    '̣'  # nặng
)


def fold_tone_marks(text: str) -> str:
    """
    Make Vietnamese tone-mark placement irrelevant when comparing names.

    Vietnamese has two equally valid conventions for where the tone mark sits
    inside a syllable — "Thùy" (mark on u) vs "Thuỳ" (mark on y), "hòa" vs
    "hoà". Zalo display names come from whatever the user's keyboard produced,
    so both spellings turn up for the same person. As Unicode they are
    different strings (ù = U+00F9, ỳ = U+1EF3), which scores only 84% on
    fuzzy matching and falls under the default 0.85 threshold.

    Within each syllable, keep the base letters in their original order and
    move any tone mark to the end. Both spellings collapse to one canonical
    form. Because letter order is preserved, "an" and "na" stay distinct.
    """
    folded = []
    for syllable in unicodedata.normalize('NFD', text).split(' '):
        base = ''.join(ch for ch in syllable if ch not in _TONE_MARKS)
        tones = ''.join(sorted(ch for ch in syllable if ch in _TONE_MARKS))
        folded.append(base + tones)
    return unicodedata.normalize('NFC', ' '.join(folded))


class Comparator:
    """Compare Excel usernames with group members using various matching strategies"""

    def __init__(self, threshold: float = 0.85, case_sensitive: bool = False):
        """
        Initialize comparator

        Args:
            threshold: Similarity threshold for fuzzy matching (0.0 to 1.0)
            case_sensitive: Whether to use case-sensitive comparison
        """
        self.threshold = threshold * 100  # fuzzywuzzy uses 0-100 scale
        self.case_sensitive = case_sensitive

    def normalize_name(self, name: str) -> str:
        """
        Normalize name for comparison

        Args:
            name: Name to normalize

        Returns:
            Normalized name
        """
        name = re.sub(r'\s+', ' ', name).strip()
        if not self.case_sensitive:
            name = name.lower()
        return fold_tone_marks(name)

    def exact_match(self, excel_names: List[str], group_members: Set[str]) -> Tuple[List[str], List[str], Set[str]]:
        """
        Find exact matches and missing members

        Returns:
            Tuple of (found_names, missing_names, matched_group_members)
        """
        # Keep first original for each normalized key from Excel
        excel_normalized_to_original = {}
        for name in excel_names:
            key = self.normalize_name(name)
            if key not in excel_normalized_to_original:
                excel_normalized_to_original[key] = name

        group_normalized_to_original = {}
        for name in group_members:
            key = self.normalize_name(name)
            if key not in group_normalized_to_original:
                group_normalized_to_original[key] = name

        found = []
        missing = []
        matched_group_members = set()

        for normalized, original_excel in excel_normalized_to_original.items():
            if normalized in group_normalized_to_original:
                found.append(original_excel)
                matched_group_members.add(group_normalized_to_original[normalized])
            else:
                missing.append(original_excel)

        return found, missing, matched_group_members

    def fuzzy_match(self, excel_names: List[str], group_members: Set[str]) -> Tuple[List[str], List[str], Dict[str, str], Set[str]]:
        """
        Find fuzzy matches and missing members

        Returns:
            Tuple of (found_names, missing_names, match_details, matched_group_members)
        """
        found = []
        missing = []
        match_details = {}
        matched_group_members = set()

        for excel_name in excel_names:
            normalized_excel = self.normalize_name(excel_name)
            best_match_score = 0
            best_match_name = None

            for group_name in group_members:
                normalized_group = self.normalize_name(group_name)

                # force_ascii=False is essential for Vietnamese names.
                # fuzzywuzzy's default (True) runs the inputs through an
                # ASCII-folder that only understands Latin-1, so it DELETES
                # 'ù' but keeps 'ủ' — "Thùy" and "Thúy" both become "thy"
                # and score 100, while "Thủy" vs "Thụy" correctly scores 75.
                # That inconsistency reports people as present in a group
                # when they are not.
                ratio = fuzz.ratio(normalized_excel, normalized_group)
                partial = fuzz.partial_ratio(normalized_excel, normalized_group)
                token_sort = fuzz.token_sort_ratio(
                    normalized_excel, normalized_group, force_ascii=False
                )
                token_set = fuzz.token_set_ratio(
                    normalized_excel, normalized_group, force_ascii=False
                )
                score = max(ratio, partial, token_sort, token_set)

                if score > best_match_score:
                    best_match_score = score
                    best_match_name = group_name

            if best_match_score >= self.threshold and best_match_name is not None:
                found.append(excel_name)
                matched_group_members.add(best_match_name)
                match_details[excel_name] = f"{best_match_name} ({best_match_score:.0f}%)"
            else:
                missing.append(excel_name)
                if best_match_name:
                    match_details[excel_name] = f"Best match: {best_match_name} ({best_match_score:.0f}%) - Below threshold"

        return found, missing, match_details, matched_group_members

    def compare(self, excel_names: List[str], group_members: Set[str], use_fuzzy: bool = True) -> Dict:
        """
        Compare Excel names with group members

        Returns:
            Dictionary with comparison results
        """
        if use_fuzzy:
            found, missing, match_details, matched_group_members = self.fuzzy_match(excel_names, group_members)
        else:
            found, missing, matched_group_members = self.exact_match(excel_names, group_members)
            match_details = {}

        # Members in group but not matched from Excel list
        extra_in_group = sorted([m for m in group_members if m not in matched_group_members])

        return {
            'total_excel': len(excel_names),
            'total_group': len(group_members),
            'found': found,
            'missing': missing,
            'extra_in_group': extra_in_group,
            'found_count': len(found),
            'missing_count': len(missing),
            'extra_in_group_count': len(extra_in_group),
            'match_details': match_details,
            'method': 'fuzzy' if use_fuzzy else 'exact',
            'threshold': self.threshold / 100 if use_fuzzy else 1.0
        }
