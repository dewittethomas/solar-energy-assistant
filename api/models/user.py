from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str | None = None
    installation_id: str | None = None
