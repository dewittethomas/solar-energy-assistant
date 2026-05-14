from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException

from pipeline import ModelTrainingPipeline
from responses.model_training_result import ModelTrainingResult
from services.dependencies import get_model_training_pipeline

router = APIRouter(prefix='/models', tags=['models'])

ModelTrainingPipelineDep = Annotated[
    ModelTrainingPipeline,
    Depends(get_model_training_pipeline)
]

@router.post(
    '/train',
    operation_id='train_solar_prediction_model',
    response_model=ModelTrainingResult
)
async def train_solar_prediction_model(
    model_training_pipeline: ModelTrainingPipelineDep,
    parquet_path: str = Form(...),
    optimize: bool = Form(False),
    advanced_optimization: bool = Form(False),
    n_trials: int = Form(50),
    activate_model: bool = Form(False)
) -> ModelTrainingResult:
    try:
        use_optuna = optimize or advanced_optimization

        return model_training_pipeline.train_model_from_parquet(
            parquet_path=Path(parquet_path),
            optimize=use_optuna,
            n_trials=n_trials,
            activate_model=activate_model
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Model training failed: {str(e)}'
        )
