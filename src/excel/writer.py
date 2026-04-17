import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Union
from datetime import datetime


class ExcelWriter:
    """Write results to Excel or CSV files"""

    def __init__(self, output_path: str, format: str = 'xlsx'):
        self.output_path = Path(output_path)
        self.format = format
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def _build_missing_dataframe(self, missing_users: List[Union[str, Dict[str, str]]]) -> pd.DataFrame:
        rows = []
        for item in missing_users:
            if isinstance(item, dict):
                rows.append({
                    'SĐT Zalo': str(item.get('phone', '') or ''),
                    'Tên Zalo': str(item.get('name', '') or ''),
                    'Status': 'Not in group'
                })
            else:
                rows.append({
                    'SĐT Zalo': '',
                    'Tên Zalo': str(item),
                    'Status': 'Not in group'
                })

        return pd.DataFrame(rows, columns=['SĐT Zalo', 'Tên Zalo', 'Status'])

    def _build_extra_in_group_dataframe(self, extra_in_group: List[Union[str, Dict[str, str]]]) -> pd.DataFrame:
        rows = []
        for item in extra_in_group:
            if isinstance(item, dict):
                rows.append({'Tên Zalo': str(item.get('name', '') or '')})
            else:
                rows.append({'Tên Zalo': str(item)})

        return pd.DataFrame(rows, columns=['Tên Zalo'])

    def write_results(
        self,
        missing_users: List[Union[str, Dict[str, str]]],
        metadata: Optional[Dict] = None,
        extra_in_group: Optional[List[Union[str, Dict[str, str]]]] = None
    ) -> bool:
        """
        Write report to Excel/CSV.

        Args:
            missing_users: List of missing users (str names or dict rows {phone, name})
            metadata: Optional metadata
            extra_in_group: Members found in group but not in Excel list
        """
        missing_df = self._build_missing_dataframe(missing_users)
        extra_df = self._build_extra_in_group_dataframe(extra_in_group or [])

        if metadata is None:
            metadata = {}

        metadata['Generated At'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        metadata['Total Missing'] = len(missing_users)
        metadata['Total In Group Not In Excel'] = len(extra_in_group or [])

        try:
            if self.format == 'xlsx':
                with pd.ExcelWriter(self.output_path, engine='openpyxl') as writer:
                    missing_df.to_excel(writer, sheet_name='Missing Members', index=False)
                    extra_df.to_excel(writer, sheet_name='In Group Not In Excel', index=False)

                    metadata_items = [{'Key': k, 'Value': str(v)} for k, v in metadata.items()]
                    metadata_df = pd.DataFrame(metadata_items)
                    metadata_df.to_excel(writer, sheet_name='Metadata', index=False)

            elif self.format == 'csv':
                # For CSV, write primary report only (missing members)
                missing_df.to_csv(self.output_path, index=False)
            else:
                raise ValueError(f"Unsupported format: {self.format}")

            return True

        except Exception as e:
            raise Exception(f"Error writing output file: {str(e)}")

    def write_comparison_report(self, found: List[str], missing: List[Union[str, Dict[str, str]]],
                                group_url: str, excel_file: str,
                                extra_in_group: Optional[List[Union[str, Dict[str, str]]]] = None) -> bool:
        metadata = {
            'Group URL': group_url,
            'Excel File': excel_file,
            'Total in Excel': len(found) + len(missing),
            'Found in Group': len(found),
            'Missing from Group': len(missing),
            'In Group Not In Excel': len(extra_in_group or [])
        }

        return self.write_results(missing, metadata, extra_in_group)
