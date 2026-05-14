from repositories.metadata_repository import MetadataRepository

class DatasetRepository:
    def __init__(
        self,
        metadata_repository: MetadataRepository | None = None
    ) -> None:
        self.metadata_repository = metadata_repository or MetadataRepository()

    def list_datasets(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> list[dict[str, object]]:
        return self.metadata_repository.list_datasets(limit, offset)

    def get(self, dataset_id: str) -> dict[str, object] | None:
        return self.metadata_repository.get_dataset(dataset_id)
