import pandas as pd
from typing import List, Tuple, Dict, Any
from pathlib import Path
import unicodedata
import re


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

        phone_aliases = {'sdt', 'sdtzalo', 'sodienthoai', 'dienthoai', 'phone'}
        name_aliases = {'ten', 'tenzalo', 'tenkhach', 'hoten', 'name'}

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

    def _extract_group_id(self, text: str) -> str:
        """
        Extract normalized group id from:
        - full URL: https://zalo.me/g/<group_id>
        - raw id: <group_id>
        """
        value = str(text or "").strip()
        m = re.search(r"zalo\.me/g/([A-Za-z0-9]+)", value)
        if m:
            return m.group(1).strip()
        return value

    def _detect_group_column(self, df: pd.DataFrame) -> str | None:
        """Return the group-link column name if present in grouped templates."""
        for col in df.columns:
            normalized = self._normalize_header(col)
            if normalized in {"groupxe", "group", "linkgroup", "groupzalo"}:
                return col
        return None

    def _get_grouped_contacts(self, df: pd.DataFrame) -> Dict[str, List[Dict[str, str]]]:
        """
        Parse grouped Excel format where group header rows contain Zalo links,
        and contact rows follow under each header.
        """
        phone_col, name_col = self._find_required_columns(df)
        group_col = self._detect_group_column(df)
        if group_col is None:
            return {}

        # Group header rows usually contain only the link in "Group xe".
        link_mask = df[group_col].astype(str).str.contains(r"zalo\.me/g/", case=False, na=False)
        if not link_mask.any():
            return {}

        group_link_per_row = df[group_col].where(link_mask).ffill()
        stt_numeric = pd.to_numeric(df.get("STT"), errors="coerce").notna() if "STT" in df.columns else pd.Series([True] * len(df))

        grouped: Dict[str, List[Dict[str, str]]] = {}
        for i, row in df.iterrows():
            if not stt_numeric.iloc[i]:
                continue

            group_id = self._extract_group_id(group_link_per_row.iloc[i])
            if not group_id:
                continue

            phone = '' if pd.isna(row[phone_col]) else str(row[phone_col]).strip()
            name = '' if pd.isna(row[name_col]) else str(row[name_col]).strip()
            if not name:
                continue

            grouped.setdefault(group_id, []).append({'phone': phone, 'name': name})

        return grouped

    def get_group_batches(self) -> List[Dict[str, Any]]:
        """
        Return grouped batches in file order for auto-run mode.

        Each item:
          {
            "group_id": str,
            "group_url": str,
            "group_label": str,
            "contacts": [{"phone": str, "name": str}, ...]
          }
        """
        df = self.read_file()
        phone_col, name_col = self._find_required_columns(df)
        group_col = self._detect_group_column(df)
        if group_col is None:
            return []

        link_mask = df[group_col].astype(str).str.contains(r"zalo\.me/g/", case=False, na=False)
        if not link_mask.any():
            return []

        batches: List[Dict[str, Any]] = []
        current_batch: Dict[str, Any] | None = None
        stt_numeric = (
            pd.to_numeric(df.get("STT"), errors="coerce").notna()
            if "STT" in df.columns
            else pd.Series([True] * len(df), index=df.index)
        )

        for i, row in df.iterrows():
            raw_group_cell = '' if pd.isna(row[group_col]) else str(row[group_col]).strip()
            is_header = bool(re.search(r"zalo\.me/g/[A-Za-z0-9]+", raw_group_cell, flags=re.IGNORECASE))

            if is_header:
                group_id = self._extract_group_id(raw_group_cell)
                group_url = f"https://chat.zalo.me/?g={group_id}"
                group_label = '' if pd.isna(row[name_col]) else str(row[name_col]).strip()
                current_batch = {
                    "group_id": group_id,
                    "group_url": group_url,
                    "group_label": group_label or group_id,
                    "contacts": []
                }
                batches.append(current_batch)
                continue

            if current_batch is None:
                continue

            if not stt_numeric.iloc[i]:
                continue

            phone = '' if pd.isna(row[phone_col]) else str(row[phone_col]).strip()
            name = '' if pd.isna(row[name_col]) else str(row[name_col]).strip()
            if not name:
                continue
            current_batch["contacts"].append({'phone': phone, 'name': name})

        return [b for b in batches if b["contacts"]]

    def get_contacts(self, group_id: str | None = None) -> List[Dict[str, str]]:
        """
        Extract and clean contacts from Excel.

        Returns:
            List of dict rows: {'phone': str, 'name': str}

        Raises:
            ValueError: If required columns cannot be found
        """
        df = self.read_file()
        grouped_contacts = self._get_grouped_contacts(df)
        if grouped_contacts:
            if group_id is None:
                contacts: List[Dict[str, str]] = []
                for gid in grouped_contacts:
                    contacts.extend(grouped_contacts[gid])
                return contacts

            normalized_group_id = self._extract_group_id(group_id)
            contacts = grouped_contacts.get(normalized_group_id, [])
            if not contacts:
                raise ValueError(
                    f"Không tìm thấy dữ liệu cho Group ID: {normalized_group_id}. "
                    "Hãy kiểm tra lại Group ID hoặc file Excel."
                )
            return contacts

        # Backward-compatible format: single contact list without grouped headers.
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
