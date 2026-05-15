from datetime import date, time

from pydantic import BaseModel

class HourlyPredictionResult(BaseModel):
    hour: time
    value: float

class DailyPredictionResult(BaseModel):
    day: date
    average: float
    predictions: list[HourlyPredictionResult]

class PredictionResult(BaseModel):
    total_average: float
    predictions: list[DailyPredictionResult]
