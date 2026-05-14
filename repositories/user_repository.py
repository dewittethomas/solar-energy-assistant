from models.user import UserCreate
from repositories.metadata_repository import MetadataRepository

class UserRepository:
    def __init__(
        self,
        metadata_repository: MetadataRepository | None = None
    ) -> None:
        self.metadata_repository = metadata_repository or MetadataRepository()

    def create_user(self, user: UserCreate) -> dict[str, object]:
        return self.metadata_repository.create_user(user)

    def list_users(self) -> list[dict[str, object]]:
        return self.metadata_repository.list_users()

    def get_user(self, user_id: str) -> dict[str, object] | None:
        return self.metadata_repository.get_user(user_id)
