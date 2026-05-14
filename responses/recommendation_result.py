from datetime import datetime

from pydantic import BaseModel

class UsageWindowRecommendationResult(BaseModel):
    installation_id: str
    preferred_strategy: str
    requested_start: datetime
    requested_end: datetime
    recommended_start: datetime
    recommended_end: datetime
    duration_hours: float
    energy_requirement_kwh: float
    expected_solar_energy_kwh: float
    expected_energy_shortfall_kwh: float
    expected_surplus_kwh: float
    expected_average_power_kw: float
    coverage_ratio: float
    message: str
