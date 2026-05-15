import csv
import re
from pathlib import Path

MONTH_NAMES = (
    'jan|januari|'
    'feb|februari|'
    'mar|march|mrt|maart|'
    'apr|april|'
    'may|mei|'
    'jun|june|juni|'
    'jul|july|juli|'
    'aug|august|augustus|'
    'sep|sept|september|'
    'oct|okt|october|oktober|'
    'nov|november|'
    'dec|december'
)
DATE_PATTERNS = [
    re.compile(r'^\d{4}-\d{2}-\d{2}', re.IGNORECASE),
    re.compile(r'^\d{1,2}[./-]\d{1,2}[./-]\d{2,4}', re.IGNORECASE),
    re.compile(rf'^({MONTH_NAMES})\.? \d{{4}}$', re.IGNORECASE),
]

class CsvHeaderDetector:
    def detect(self, file_path: Path, max_rows: int = 50) -> tuple[int, csv.Dialect]:
        sample = file_path.read_text(
            encoding='utf-8-sig',
            errors='ignore'
        )

        sniffer = csv.Sniffer()

        try:
            dialect = sniffer.sniff(sample)
        except Exception:
            dialect = csv.excel

        rows = list(csv.reader(sample.splitlines(), dialect))

        for index in range(min(len(rows) - 1, max_rows)):
            current_row = rows[index]
            next_rows = rows[index + 1:index + 6]

            if self._row_looks_like_header(current_row, next_rows):
                return index, dialect

        raise ValueError(f'Could not detect header row in {file_path}')

    def _row_looks_like_header(
        self,
        current_row: list[str],
        next_rows: list[list[str]]
    ) -> bool:
        current_cells = self._filled_cells(current_row)

        if len(current_cells) < 2:
            return False

        if current_cells[0].lower().startswith('sep='):
            return False

        matching_next_rows = [
            row
            for row in next_rows
            if len(self._filled_cells(row)) == len(current_cells)
        ]

        if not matching_next_rows:
            return False

        required_ratio = 0.75 if len(current_cells) == 2 else 0.5
        first_matching_row = matching_next_rows[0]

        if self._data_like_ratio(first_matching_row) < required_ratio:
            return False

        return any(
            self._data_like_ratio(row) >= required_ratio
            for row in matching_next_rows[:5]
        )

    def _data_like_ratio(self, row: list[str]) -> float:
        cells = self._filled_cells(row)

        if not cells:
            return 0

        data_like_count = sum(
            1
            for cell in cells
            if self._is_data_like(cell)
        )

        return data_like_count / len(cells)

    def _filled_cells(self, row: list[str]) -> list[str]:
        return [
            cell.strip()
            for cell in row
            if cell.strip()
        ]

    def _is_data_like(self, value: str) -> bool:
        return self._is_number(value) or self._is_date_like(value)

    def _is_number(self, value: str) -> bool:
        normalized = value.strip().replace(' ', '')

        if not normalized:
            return False

        if ',' in normalized and '.' in normalized:
            decimal_separator = ',' if normalized.rfind(',') > normalized.rfind('.') else '.'
            thousands_separator = '.' if decimal_separator == ',' else ','
            normalized = normalized.replace(thousands_separator, '')
            normalized = normalized.replace(decimal_separator, '.')
        else:
            normalized = normalized.replace(',', '.')

        try:
            float(normalized)
            return True
        except ValueError:
            return False

    def _is_date_like(self, value: str) -> bool:
        normalized = value.strip()

        return any(
            pattern.match(normalized)
            for pattern in DATE_PATTERNS
        )
