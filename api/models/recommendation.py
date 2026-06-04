from datetime import date as Date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

class RecommendationStrategy(StrEnum):
    maximize_solar_usage = 'maximize_solar_usage'

class SelectedDevice(BaseModel):
    name: str
    consumption_kwh: float = Field(gt=0)
    duration_minutes: int | None = Field(default=None, gt=0)

class UsageWindowRecommendationRequest(BaseModel):
    installation_id: str
    start: datetime | None = None
    end: datetime | None = None
    date: Date | None = None
    preferred_start: datetime | None = None
    preferred_end: datetime | None = None
    energy_requirement_kwh: float | None = Field(default=None, gt=0)
    preferred_strategy: RecommendationStrategy = (
        RecommendationStrategy.maximize_solar_usage
    )
    selected_devices: list[SelectedDevice] = Field(default_factory=list)
