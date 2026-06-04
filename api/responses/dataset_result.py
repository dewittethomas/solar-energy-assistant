from pydantic import BaseModel

class DatasetResult(BaseModel):
    id: str
    installation_id: str
    dataset_hash: str
    path: str
    row_count: int
    granularity: str
    value_column: str
    production_unit: str | None = None
    created_at: str
    period_start: str | None = None
    period_end: str | None = None
    source_name: str | None = None
    original_columns: list[str] = []
    internal_columns: list[str] = []
    date_column: str | None = None
    time_column: str | None = None
    measurement_column: str | None = None
