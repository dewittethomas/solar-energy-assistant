from pydantic import BaseModel

class CsvPreviewRowResult(BaseModel):
    values: dict[str, str | None]

class CsvColumnsResult(BaseModel):
    filename: str
    columns: list[str]
    preview_rows: list[CsvPreviewRowResult] = []

class TimeResolutionResult(BaseModel):
    kind: str
    interval_minutes: float | None

class DataUploadResult(BaseModel):
    dataset_id: str
    dataset_hash: str
    dataset_already_exists: bool
    installation_id: str
    source_name: str | None = None
    production_unit: str
    rows: int
    columns: list[str]
    original_columns: list[str] = []
    internal_columns: list[str] = []
    value_column: str
    date_column: str | None = None
    time_column: str | None = None
    measurement_column: str | None = None
    time_resolution: TimeResolutionResult
    parquet_path: str
