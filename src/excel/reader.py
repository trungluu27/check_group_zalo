import pandas as pd
from typing import List, Tuple, Dict
from pathlib import Path
import unicodedata


class ExcelReader:
    """Read and parse Excel files containing Zalo contact data"""

    def __init__(self, file_path: str):
        """
        Initialize Excel reader

        Args:
            file_path: Path to Excel file
        """
        self.file_path = Path(file_path)

    def read_file(self) -> pd.DataFrame:
        """
        Read Excel file and return DataFrame
        """
        try:
            if self.file_path.suffix == '.xlsx':
                return pd.read_excel(self.file_path, engine='openpyxl')
            elif self.file_path.suffix == '.xls':
                return pd.read_excel(self.file_path, engine='xlrd')
            else:
                raise ValueError(f"Unsupported file format: {self.file_path.suffix}")
        except Exception as e:
            raise Exception(f"Error reading Excel file: {str(e)}")

    def _normalize_header(self, header: str) -> str:
        """
        Normalize column header for robust matching.
        - Case-insensitive
        - Accent-insensitive (e.g. 'tên' -> 'ten', 'SĐT' -> 'sdt')
        - Ignores spaces, underscores, dashes, dots
        """
        text = str(header).strip().lower()
        text = unicodedata.normalize('NFD', text)
        text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
        text = text.replace('đ', 'd')
        for ch in [' ', '_', '-', '.']:
            text = text.replace(ch, '')
        return text

    def _find_required_columns(self, df: pd.DataFrame) -> Tuple[str, str]:
        """
        Find required columns in Excel:
        - Phone column: SĐT / SDT / SĐT Zalo
        - Name column: tên / tên zalo
        """
        normalized_to_original = {
            self._normalize_header(col): col
            for col in df.columns
        }

        phone_aliases = {'sdt', 'sdtzalo'}
        name_aliases = {'ten', 'tenzalo'}

        phone_col = None
        name_col = None

        for normalized, original in normalized_to_original.items():
            if phone_col is None and normalized in phone_aliases:
                phone_col = original
            if name_col is None and normalized in name_aliases:
                name_col = original

        missing = []
        if phone_col is None:
            missing.append("cột SĐT (SĐT / SDT / SĐT Zalo)")
        if name_col is None:
            missing.append("cột tên (tên / tên zalo)")

        if missing:
            raise ValueError(
                "Không tìm thấy " + " và ".join(missing) +
                f". Các cột hiện có: {list(df.columns)}"
            )

        return phone_col, name_col

    def get_contacts(self) -> List[Dict[str, str]]:
        """
        Extract and clean contacts from Excel.

        Returns:
            List of dict rows: {'phone': str, 'name': str}

        Raises:
            ValueError: If required columns cannot be found
        """
        df = self.read_file()
        phone_col, name_col = self._find_required_columns(df)

        print(f"Detected phone column: '{phone_col}'")
        print(f"Detected name column: '{name_col}'")

        filtered = df[[phone_col, name_col]].dropna(how='all')

        contacts: List[Dict[str, str]] = []
        for _, row in filtered.iterrows():
            phone = '' if pd.isna(row[phone_col]) else str(row[phone_col]).strip()
            name = '' if pd.isna(row[name_col]) else str(row[name_col]).strip()

            if not phone and not name:
                continue
            if not name:
                # Skip rows without name because matching is name-based
                continue

            contacts.append({'phone': phone, 'name': name})

        return contacts

    def get_usernames(self) -> List[str]:
        """
        Backward-compatible helper: return only names from contacts.
        """
        contacts = self.get_contacts()
        return [c['name'] for c in contacts if c['name']]

    def get_column_names(self) -> List[str]:
        df = self.read_file()
        return list(df.columns)
