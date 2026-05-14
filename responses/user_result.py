from pydantic import BaseModel

class UserResult(BaseModel):
    id: str
    first_name: str
    last_name: str | None
    display_name: str
    installation_id: str
    created_at: str
