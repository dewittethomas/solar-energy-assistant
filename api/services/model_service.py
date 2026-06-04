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
        model = self.get_model(model_id)

        if not model:
            return None

        metrics = self.repository.list_metrics(model_id)
        created_at = str(model['created_at'])

        if model.get('accuracy') is not None:
            metrics.append({
                'id': f'{model_id}:accuracy',
                'model_id': model_id,
                'metric_name': 'accuracy',
                'metric_value': model['accuracy'],
                'created_at': created_at,
                'accuracy': model['accuracy'],
                'offset_kw': model.get('offset_kw')
            })

        if model.get('offset_kw') is not None:
            metrics.append({
                'id': f'{model_id}:offset_kw',
                'model_id': model_id,
                'metric_name': 'offset_kw',
                'metric_value': model['offset_kw'],
                'created_at': created_at,
                'accuracy': model.get('accuracy'),
                'offset_kw': model['offset_kw']
            })

        return metrics

    def activate_model(self, model_id: str) -> dict[str, object] | None:
        return self.repository.activate(model_id)

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
