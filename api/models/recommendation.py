from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

class RecommendationStrategy(StrEnum):
    maximize_solar_usage = 'maximize_solar_usage'

class UsageWindowRecommendationRequest(BaseModel):
    installation_id: str
    start: datetime
    end: datetime
    energy_requirement_kwh: float = Field(gt=0)
    preferred_strategy: RecommendationStrategy
