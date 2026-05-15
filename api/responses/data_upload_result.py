from pydantic import BaseModel

class CsvColumnsResult(BaseModel):
    filename: str
    columns: list[str]

class TimeResolutionResult(BaseModel):
    kind: str
    interval_minutes: float | None

class DataUploadResult(BaseModel):
    dataset_id: str
    dataset_hash: str
    dataset_already_exists: bool
    installation_id: str
    rows: int
    columns: list[str]
    value_column: str
    time_resolution: TimeResolutionResult
    parquet_path: str
