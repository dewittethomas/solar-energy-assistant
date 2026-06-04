from datetime import datetime

from pydantic import BaseModel

class PredictionPointResult(BaseModel):
    timestamp: datetime
    value: float

class PredictionResult(BaseModel):
    unit: str = 'W'
    total_average: float
    predictions: list[PredictionPointResult]
