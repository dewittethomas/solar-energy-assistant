from pydantic import BaseModel

class DatasetResult(BaseModel):
    id: str
    installation_id: str
    dataset_hash: str
    path: str
    row_count: int
    granularity: str
    value_column: str
    created_at: str
