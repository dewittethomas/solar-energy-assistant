from pydantic import BaseModel

class OwnerResult(BaseModel):
    id: str
    first_name: str
    last_name: str | None
    display_name: str
    created_at: str
    updated_at: str
