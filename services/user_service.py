from models.user import UserCreate
from repositories.user_repository import UserRepository

class UserService:
    def __init__(
        self,
        repository: UserRepository | None = None
    ) -> None:
        self.repository = repository or UserRepository()

    def create_user(self, user: UserCreate) -> dict[str, object]:
        return self.repository.create_user(user)

    def list_users(self) -> list[dict[str, object]]:
        return self.repository.list_users()

    def get_user(self, user_id: str) -> dict[str, object] | None:
        return self.repository.get_user(user_id)
