from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Query

from pipeline import ModelTrainingPipeline
from responses.model_metric_result import ModelMetricResult
from responses.model_result import ModelResult
from responses.model_training_result import ModelTrainingResult
from services.dependencies import get_model_service, get_model_training_pipeline
from services.model_service import ModelService

router = APIRouter(prefix='/models', tags=['models'])

ModelTrainingPipelineDep = Annotated[
    ModelTrainingPipeline,
    Depends(get_model_training_pipeline)
]
ModelServiceDep = Annotated[
    ModelService,
    Depends(get_model_service)
]

@router.post(
    '/train',
    operation_id='train_model',
    response_model=ModelTrainingResult
)
async def train_model(
    model_training_pipeline: ModelTrainingPipelineDep,
    parquet_path: str = Form(...),
    optimize: bool = Form(False),
    advanced_optimization: bool = Form(False),
    n_trials: int = Form(50),
    activate_model: bool = Form(False)
) -> ModelTrainingResult:
    return _train_model(
        model_training_pipeline,
        parquet_path,
        optimize,
        advanced_optimization,
        n_trials,
        activate_model
    )

@router.get(
    '',
    operation_id='list_models',
    response_model=list[ModelResult]
)
async def list_models(
    model_service: ModelServiceDep,
    installation_id: str | None = Query(None),
    is_active: bool | None = Query(None),
    target_column: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
) -> list[ModelResult]:
    return model_service.list_models(
        limit=limit,
        offset=offset,
        installation_id=installation_id,
        is_active=is_active,
        target_column=target_column
    )

@router.get(
    '/{model_id}',
    operation_id='get_model',
    response_model=ModelResult
)
async def get_model(
    model_id: str,
    model_service: ModelServiceDep
) -> ModelResult:
    model = model_service.get_model(model_id)

    if not model:
        raise HTTPException(status_code=404, detail='Model not found')

    return model

@router.get(
    '/{model_id}/metrics',
    operation_id='list_model_metrics',
    response_model=list[ModelMetricResult]
)
async def list_model_metrics(
    model_id: str,
    model_service: ModelServiceDep
) -> list[ModelMetricResult]:
    metrics = model_service.list_model_metrics(model_id)

    if metrics is None:
        raise HTTPException(status_code=404, detail='Model not found')

    return metrics

def _train_model(
    model_training_pipeline: ModelTrainingPipeline,
    parquet_path: str,
    optimize: bool,
    advanced_optimization: bool,
    n_trials: int,
    activate_model: bool
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
