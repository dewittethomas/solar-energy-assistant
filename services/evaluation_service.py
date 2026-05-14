from responses.model_training_result import ModelQualityResult
from core.settings import get_settings

class EvaluationService:
    def __init__(self, minimum_r2: float | None = None) -> None:
        self.minimum_r2 = (
            minimum_r2
            if minimum_r2 is not None
            else get_settings().minimum_model_r2
        )

    def build_model_quality(
        self,
        diagnosis: dict[str, object],
        metrics: dict[str, float]
    ) -> ModelQualityResult:
        if metrics['r2'] < self.minimum_r2:
            return ModelQualityResult(
                status='warning',
                message=(
                    'The model is not accurate enough to become active yet. '
                    'Add more representative data or train again later.'
                )
            )

        status = diagnosis.get('status')

        if status == 'likely_overfitting':
            return ModelQualityResult(
                status='warning',
                message=(
                    'The model may be too specific to this dataset and could '
                    'perform worse on new data.'
                )
            )

        if status == 'possible_overfitting':
            return ModelQualityResult(
                status='warning',
                message=(
                    'The model looks useful, but predictions should be checked '
                    'with new measurements.'
                )
            )

        if status == 'possible_distribution_shift':
            return ModelQualityResult(
                status='warning',
                message=(
                    'Recent data behaves differently from earlier data. Check '
                    'predictions with recent measurements before relying on it.'
                )
            )

        return ModelQualityResult(
            status='good',
            message='The model looks consistent on the available data.'
        )

    def can_activate(self, model_quality: ModelQualityResult) -> bool:
        return model_quality.status == 'good'
