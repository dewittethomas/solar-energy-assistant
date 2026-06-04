from models.owner import OwnerPayload
from repositories.owner_repository import OwnerRepository


class OwnerService:
    def __init__(
        self,
        repository: OwnerRepository | None = None
    ) -> None:
        self.repository = repository or OwnerRepository()

    def get_owner(self) -> dict[str, object] | None:
        return self.repository.get_owner()

    def create_owner(self, owner: OwnerPayload) -> dict[str, object]:
        return self.repository.create_owner(owner)

    def update_owner(self, owner: OwnerPayload) -> dict[str, object]:
        return self.repository.update_owner(owner)
