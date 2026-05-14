import json
import re
from pathlib import Path
from uuid import uuid4

from core.settings import get_settings
from models.column_mapping import ColumnMapping
from pipeline import CsvPreprocessingPipeline
from responses.data_upload_result import (
    CsvColumnsResult,
    DataUploadResult,
    TimeResolutionResult,
)
from services.metadata_service import MetadataService

class DataUploadService:
    def __init__(
        self,
        pipeline: CsvPreprocessingPipeline | None = None,
        metadata_service: MetadataService | None = None
    ) -> None:
        self._pipeline = pipeline
        self._metadata_service = metadata_service or MetadataService()
        self._settings = get_settings()

    def get_csv_columns(
        self,
        filename: str,
        contents: bytes
    ) -> CsvColumnsResult:
        source_path = self._write_temp_upload(filename, contents)

        try:
            columns = self._pipeline.get_csv_columns(source_path)

            return CsvColumnsResult(
                filename=filename,
                columns=columns
            )
        finally:
            source_path.unlink(missing_ok=True)

    def process_csv_upload(
        self,
        filename: str,
        contents: bytes,
        installation_id: str,
        mapping: str | dict[str, object]
    ) -> DataUploadResult:
        return self.process_csv_uploads(
            uploads=[(filename, contents)],
            installation_id=installation_id,
            mapping=mapping
        )

    def process_csv_uploads(
        self,
        uploads: list[tuple[str, bytes]],
        installation_id: str,
        mapping: str | dict[str, object]
    ) -> DataUploadResult:
        if not uploads:
            raise ValueError('At least one file is required')

        source_paths = []

        try:
            for filename, contents in uploads:
                source_paths.append(
                    self._write_temp_upload(filename, contents)
                )

            column_mapping = self._parse_mapping(mapping)
            canonical = self._pipeline.canonicalize_csv_files(
                source_paths,
                installation_id,
                column_mapping
            )
            time_resolution = self._pipeline.detect_time_resolution(canonical)
            hourly = self._pipeline.resample_to_hourly(canonical)
            output_path = self._build_output_path(
                self._build_output_filename(uploads),
                installation_id
            )
            parquet_path = self._pipeline.save_parquet(hourly, output_path)
            value_column = self._get_value_column(hourly.columns.tolist())
            dataset = self._metadata_service.register_dataset(
                df=hourly,
                installation_id=installation_id,
                path=parquet_path,
                granularity=str(time_resolution['kind']),
                value_column=value_column
            )

            return DataUploadResult(
                dataset_id=str(dataset['id']),
                dataset_hash=str(dataset['dataset_hash']),
                dataset_already_exists=bool(dataset['already_exists']),
                installation_id=installation_id,
                rows=len(hourly),
                columns=hourly.columns.tolist(),
                value_column=value_column,
                time_resolution=TimeResolutionResult(
                    kind=str(time_resolution['kind']),
                    interval_minutes=time_resolution['intervalMinutes']
                ),
                parquet_path=self._format_parquet_path(parquet_path)
            )
        finally:
            for source_path in source_paths:
                source_path.unlink(missing_ok=True)

    def _write_temp_upload(
        self,
        filename: str,
        contents: bytes
    ) -> Path:
        if not contents:
            raise ValueError('Uploaded file is empty')

        upload_dir = self._settings.upload_storage_dir / 'tmp'
        upload_dir.mkdir(parents=True, exist_ok=True)

        safe_filename = self._safe_name(Path(filename).stem or 'upload')
        source_path = upload_dir / f'{safe_filename}-{uuid4().hex}.csv'
        source_path.write_bytes(contents)

        return source_path

    def _parse_mapping(
        self,
        mapping: str | dict[str, object]
    ) -> ColumnMapping:
        if isinstance(mapping, str):
            try:
                mapping = json.loads(mapping)
            except json.JSONDecodeError as exc:
                raise ValueError('Mapping must be valid JSON') from exc

        if not isinstance(mapping, dict):
            raise ValueError('Mapping must be a JSON object')

        return ColumnMapping.from_payload(mapping)

    def _build_output_path(
        self,
        filename: str,
        installation_id: str
    ) -> Path:
        safe_installation_id = self._safe_name(installation_id)
        safe_filename = self._safe_name(Path(filename).stem or 'upload')

        return (
            self._settings.upload_storage_dir
            / safe_installation_id
            / f'{safe_filename}-{uuid4().hex}.parquet'
        )

    def _build_output_filename(
        self,
        uploads: list[tuple[str, bytes]]
    ) -> str:
        if len(uploads) == 1:
            return uploads[0][0]

        return 'combined-upload'

    def _safe_name(self, value: str) -> str:
        safe_value = re.sub(r'[^A-Za-z0-9_.-]+', '-', value).strip('.-')

        return safe_value or 'upload'

    def _format_parquet_path(self, parquet_path: Path) -> str:
        try:
            return parquet_path.relative_to(Path.cwd()).as_posix()
        except ValueError:
            return parquet_path.as_posix()

    def _get_value_column(self, columns: list[str]) -> str:
        value_columns = [
            column
            for column in ('power_kw', 'energy_kwh')
            if column in columns
        ]

        if len(value_columns) != 1:
            raise ValueError(
                'Expected exactly one value column: power_kw or energy_kwh'
            )

        return value_columns[0]
