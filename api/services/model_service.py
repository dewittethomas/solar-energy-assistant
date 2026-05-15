from repositories.model_repository import ModelRepository

class ModelService:
    def __init__(
        self,
        repository: ModelRepository | None = None
    ) -> None:
        self.repository = repository or ModelRepository()

    def list_models(
        self,
        limit: int = 100,
        offset: int = 0,
        installation_id: str | None = None,
        is_active: bool | None = None,
        target_column: str | None = None
    ) -> list[dict[str, object]]:
        return self.repository.list_models(
            limit=limit,
            offset=offset,
            installation_id=installation_id,
            is_active=is_active,
            target_column=target_column
        )

    def get_model(self, model_id: str) -> dict[str, object] | None:
        return self.repository.get(model_id)

    def list_model_metrics(self, model_id: str) -> list[dict[str, object]] | None:
        if not self.get_model(model_id):
            return None

        return self.repository.list_metrics(model_id)

    def get_active_model(
        self,
        installation_id: str,
        target_column: str
    ) -> dict[str, object] | None:
        models = self.list_models(
            limit=1,
            installation_id=installation_id,
            is_active=True,
            target_column=target_column
        )

        return models[0] if models else None
