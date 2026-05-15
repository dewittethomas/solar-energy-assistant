from repositories.metadata_repository import MetadataRepository

class ModelRepository:
    def __init__(
        self,
        metadata_repository: MetadataRepository | None = None
    ) -> None:
        self.metadata_repository = metadata_repository or MetadataRepository()

    def list_models(
        self,
        limit: int = 100,
        offset: int = 0,
        installation_id: str | None = None,
        is_active: bool | None = None,
        target_column: str | None = None
    ) -> list[dict[str, object]]:
        return self.metadata_repository.list_models(
            limit=limit,
            offset=offset,
            installation_id=installation_id,
            is_active=is_active,
            target_column=target_column
        )

    def get(self, model_id: str) -> dict[str, object] | None:
        return self.metadata_repository.get_model(model_id)

    def list_metrics(self, model_id: str) -> list[dict[str, object]]:
        return self.metadata_repository.list_model_metrics(model_id)
