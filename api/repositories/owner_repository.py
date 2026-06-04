from models.owner import OwnerPayload
from repositories.metadata_repository import MetadataRepository


class OwnerRepository:
    def __init__(
        self,
        metadata_repository: MetadataRepository | None = None
    ) -> None:
        self.metadata_repository = metadata_repository or MetadataRepository()

    def get_owner(self) -> dict[str, object] | None:
        return self.metadata_repository.get_owner()

    def create_owner(self, owner: OwnerPayload) -> dict[str, object]:
        return self.metadata_repository.create_owner(owner)

    def update_owner(self, owner: OwnerPayload) -> dict[str, object]:
        return self.metadata_repository.update_owner(owner)
