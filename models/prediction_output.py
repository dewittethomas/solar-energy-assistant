from pydantic import BaseModel

class PredictionOutput(BaseModel):
    wattage: float