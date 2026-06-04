from datetime import datetime

from pydantic import BaseModel

class DeviceScheduleResult(BaseModel):
    device: str
    consumption_kwh: float
    start: datetime
    end: datetime
    reason: str

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
    confidence: float
    short_reason: str
    recommended_time_window: str
    expected_production_kwh: float
    device_schedule: list[DeviceScheduleResult]
    message: str
