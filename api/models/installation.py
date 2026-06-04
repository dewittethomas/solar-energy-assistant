from pydantic import AliasChoices, BaseModel, Field


class InstallationBase(BaseModel):
    name: str = Field(min_length=1)
    country: str = Field(min_length=1)
    city: str = Field(min_length=1)
    panel_count: int | None = Field(default=None, ge=0)
    capacity_kwp: float | None = Field(
        default=None,
        ge=0,
        validation_alias=AliasChoices('capacity_kwp', 'installation_kwp'),
    )


class InstallationCreate(InstallationBase):
    pass
