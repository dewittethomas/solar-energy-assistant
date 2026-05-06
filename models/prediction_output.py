from pydantic import BaseModel
from datetime import datetime

class PredictionOutput(BaseModel):
    timestamp: datetime
    value: float