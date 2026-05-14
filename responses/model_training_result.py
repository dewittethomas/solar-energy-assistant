from pydantic import BaseModel

class ModelTrainingMetrics(BaseModel):
    r2: float
    mae: float
    mse: float
    rmse: float

class ModelQualityResult(BaseModel):
    status: str
    message: str

class ModelTrainingResult(BaseModel):
    model_path: str
    source_path: str
    training_rows: int
    train_rows: int
    validation_rows: int
    test_rows: int
    feature_columns: list[str]
    target_column: str
    optimized: bool
    training_mode: str
    best_params: dict[str, int | float]
    metrics: ModelTrainingMetrics
    model_quality: ModelQualityResult
