from pydantic import BaseModel

class ModelResult(BaseModel):
    id: str
    dataset_id: str
    installation_id: str
    version: str
    model_path: str
    is_active: bool
    created_at: str
    mae: float
    rmse: float
    r2: float
    mse: float
    train_size: int
    validation_size: int
    test_size: int
    target_column: str
    metrics: dict[str, float]
