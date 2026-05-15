from pydantic import BaseModel

class ModelMetricResult(BaseModel):
    id: str
    model_id: str
    metric_name: str
    metric_value: float
    created_at: str
