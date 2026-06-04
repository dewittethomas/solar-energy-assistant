from pydantic import AliasChoices, BaseModel, Field, model_validator


class ApplianceConsumption(BaseModel):
    car: float = Field(default=0, ge=0)
    washing_machine: float = Field(default=0, ge=0)
    dishwasher: float = Field(default=0, ge=0)
    dryer: float = Field(default=0, ge=0)
    boiler: float = Field(default=0, ge=0)


class ConsumingActivity(BaseModel):
    id: str | None = None
    name: str = Field(min_length=1)
    consumption_kwh: float = Field(ge=0)
    duration_minutes: int | None = Field(default=None, ge=0)
    category: str | None = None
    is_custom: bool = True


class InstallationConfigurationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    country: str | None = Field(default=None, min_length=1)
    city: str | None = Field(default=None, min_length=1)
    panel_count: int | None = Field(default=None, ge=0)
    capacity_kwp: float | None = Field(
        default=None,
        ge=0,
        validation_alias=AliasChoices('capacity_kwp', 'installation_kwp'),
    )
    consuming_activities: list[ConsumingActivity] = Field(default_factory=list)
    appliances: ApplianceConsumption | None = None

    @property
    def installation_kwp(self) -> float | None:
        return self.capacity_kwp

    @model_validator(mode='after')
    def include_legacy_appliances(self) -> 'InstallationConfigurationUpdate':
        if self.consuming_activities or self.appliances is None:
            return self

        self.consuming_activities = [
            ConsumingActivity(name=name, consumption_kwh=value)
            for name, value in self.appliances.model_dump().items()
            if value > 0
        ]

        return self
