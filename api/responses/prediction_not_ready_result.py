from pydantic import BaseModel


class PredictionNotReadyResult(BaseModel):
    status: str
    reason: str
    training_run_id: str
