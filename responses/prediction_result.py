from pydantic import BaseModel
from datetime import date, time
from typing import List

class HourlyPredictionResult(BaseModel):
    hour: time
    value: float

class DailyPredictionResult(BaseModel):
    day: date
    average: float
    predictions: List[HourlyPredictionResult]

class PredictionResult(BaseModel):
    total_average: float
    predictions: List[DailyPredictionResult]