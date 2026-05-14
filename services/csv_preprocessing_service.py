from pathlib import Path

import pandas as pd

from ingestion.canonicalizer import DataFrameCanonicalizer
from ingestion.csv_data_reader import CsvDataReader
from ingestion.hourly_resampler import HourlyResampler
from ingestion.time_resolution_detector import TimeResolutionDetector
from models.column_mapping import ColumnMapping
from services.parquet_service import ParquetService

class CsvPreprocessingService:
    def __init__(
        self,
        csv_reader: CsvDataReader | None = None,
        canonicalizer: DataFrameCanonicalizer | None = None,
        time_resolution_detector: TimeResolutionDetector | None = None,
        hourly_resampler: HourlyResampler | None = None,
        parquet_service: ParquetService | None = None
    ) -> None:
        self._csv_reader = csv_reader or CsvDataReader()
        self._canonicalizer = canonicalizer or DataFrameCanonicalizer()
        self._time_resolution_detector = (
            time_resolution_detector or TimeResolutionDetector()
        )
        self._hourly_resampler = hourly_resampler or HourlyResampler()
        self._parquet_service = parquet_service or ParquetService()

    def read_csv(self, file_path: Path) -> pd.DataFrame:
        return self._csv_reader.read(file_path)

    def get_columns(self, file_path: Path) -> list[str]:
        return self._csv_reader.get_columns(file_path)

    def canonicalize_csv(
        self,
        file_path: Path,
        installation_id: str,
        mapping: ColumnMapping | dict[str, object]
    ) -> pd.DataFrame:
        if isinstance(mapping, dict):
            mapping = ColumnMapping.from_payload(mapping)

        df = self._csv_reader.read(file_path)

        return self._canonicalizer.canonicalize(
            df,
            installation_id,
            mapping
        )

    def canonicalize_csv_files(
        self,
        file_paths: list[Path],
        installation_id: str,
        mapping: ColumnMapping | dict[str, object]
    ) -> pd.DataFrame:
        if not file_paths:
            raise ValueError('At least one CSV file is required')

        if isinstance(mapping, dict):
            mapping = ColumnMapping.from_payload(mapping)

        frames = [
            self.canonicalize_csv(file_path, installation_id, mapping)
            for file_path in file_paths
        ]
        combined = pd.concat(frames, ignore_index=True)

        return (
            combined
            .drop_duplicates(
                subset=['installation_id', 'timestamp'],
                keep='last'
            )
            .sort_values('timestamp')
            .reset_index(drop=True)
        )

    def detect_time_resolution(
        self,
        df: pd.DataFrame
    ) -> dict[str, float | str | None]:
        resolution = self._time_resolution_detector.detect(df)

        return {
            'kind': resolution.kind,
            'intervalMinutes': resolution.interval_minutes
        }

    def resample_to_hourly(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._hourly_resampler.resample(df)

    def save_parquet(
        self,
        df: pd.DataFrame,
        output_path: Path
    ) -> Path:
        return self._parquet_service.save_dataframe(df, output_path)

    def canonicalize_csv_to_parquet(
        self,
        file_path: Path,
        installation_id: str,
        mapping: ColumnMapping | dict[str, object],
        output_path: Path
    ) -> Path:
        df = self.canonicalize_csv(file_path, installation_id, mapping)
        df = self.resample_to_hourly(df)

        return self.save_parquet(df, output_path)
