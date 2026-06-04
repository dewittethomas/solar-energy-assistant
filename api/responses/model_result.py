from pydantic import BaseModel

class ModelResult(BaseModel):
    id: str
    dataset_id: str
    installation_id: str
    dataset_path: str | None = None
    name: str
    model_name: str
    version: str
    model_path: str
    is_active: bool
    created_at: str
    accuracy: float | None = None
    offset_kw: float | None = None
    mae: float
    rmse: float
    r2: float
    mse: float
    train_size: int
    validation_size: int
    test_size: int
    target_column: str
    metrics: dict[str, float]
