from pathlib import Path

import pandas as pd

from ingestion.csv_header_detector import CsvHeaderDetector

class CsvDataReader:
    def __init__(
        self,
        header_detector: CsvHeaderDetector | None = None
    ) -> None:
        self._header_detector = header_detector or CsvHeaderDetector()

    def read(self, file_path: Path, nrows: int | None = None) -> pd.DataFrame:
        header_row, dialect = self._header_detector.detect(file_path)

        df = pd.read_csv(
            file_path,
            sep=dialect.delimiter,
            skiprows=header_row,
            encoding='utf-8-sig',
            nrows=nrows
        )

        df.columns = df.columns.astype(str).str.strip()

        return df

    def get_columns(self, file_path: Path) -> list[str]:
        df = self.read(file_path, nrows=0)

        return [
            column
            for column in df.columns.astype(str).str.strip().tolist()
            if column and not column.startswith('Unnamed:')
        ]

