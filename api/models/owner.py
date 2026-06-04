from pydantic import BaseModel, Field

class OwnerPayload(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str | None = None
