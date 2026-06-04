from pydantic import BaseModel

from models.installation_configuration import (
    ApplianceConsumption,
    ConsumingActivity,
)


class InstallationConfigurationResult(BaseModel):
    id: str
    owner_id: str
    installation_id: str
    is_active: bool | None = None
    name: str | None
    country: str | None
    city: str | None
    latitude: float | None
    longitude: float | None
    panel_count: int | None
    capacity_kwp: float | None
    available_consuming_activities: list[ConsumingActivity]
    consuming_activities: list[ConsumingActivity]
    appliances: ApplianceConsumption
