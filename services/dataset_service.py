from repositories.dataset_repository import DatasetRepository

class DatasetService:
    def __init__(
        self,
        repository: DatasetRepository | None = None
    ) -> None:
        self.repository = repository or DatasetRepository()

    def list_datasets(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> list[dict[str, object]]:
        return self.repository.list_datasets(limit, offset)

    def get_dataset(self, dataset_id: str) -> dict[str, object] | None:
        return self.repository.get(dataset_id)
