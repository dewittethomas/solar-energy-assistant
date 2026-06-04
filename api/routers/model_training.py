from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Query

from pipeline import ModelTrainingPipeline
from responses.model_metric_result import ModelMetricResult
from responses.model_result import ModelResult
from responses.model_training_result import ModelTrainingResult
from responses.training_run_result import (
    TrainingRunQueuedResult,
    TrainingRunStatusResult,
)
from services.dependencies import (
    get_metadata_service,
    get_model_service,
    get_model_training_pipeline,
)
from services.metadata_service import MetadataService
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
MetadataServiceDep = Annotated[
    MetadataService,
    Depends(get_metadata_service)
]

@router.post(
    '/train',
    operation_id='train_model',
    response_model=TrainingRunQueuedResult
)
async def train_model(
    background_tasks: BackgroundTasks,
    model_training_pipeline: ModelTrainingPipelineDep,
    parquet_path: str = Form(...),
    optimize: bool = Form(False),
    advanced_optimization: bool = Form(False),
    n_trials: int = Form(50),
    activate_model: bool = Form(False)
) -> TrainingRunQueuedResult:
    try:
        use_optuna = optimize or advanced_optimization
        training_run = model_training_pipeline.queue_training_run(
            Path(parquet_path)
        )
        background_tasks.add_task(
            _run_training_job,
            model_training_pipeline,
            str(training_run['id']),
            parquet_path,
            use_optuna,
            n_trials,
            activate_model,
        )
        return TrainingRunQueuedResult(
            training_run_id=str(training_run['id']),
            status=str(training_run['status'])
        )
    except ValueError as e:
        detail = str(e)
        status_code = 409 if 'already in progress' in detail else 400
        raise HTTPException(status_code=status_code, detail=detail)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Model training failed to start: {str(e)}'
        )

@router.get(
    '/training-runs/{training_run_id}',
    operation_id='get_training_run_status',
    response_model=TrainingRunStatusResult
)
async def get_training_run_status(
    training_run_id: str,
    metadata_service: MetadataServiceDep
) -> TrainingRunStatusResult:
    training_run = metadata_service.get_training_run(training_run_id)

    if not training_run:
        raise HTTPException(status_code=404, detail='Training run not found')

    summary = training_run.get('summary')

    return TrainingRunStatusResult(
        training_run_id=str(training_run['id']),
        status=str(training_run['status']),
        phase=str(training_run['phase']),
        progress=int(training_run['progress']),
        current_trial=(
            int(training_run['current_trial'])
            if training_run.get('current_trial') is not None
            else None
        ),
        total_trials=(
            int(training_run['total_trials'])
            if training_run.get('total_trials') is not None
            else None
        ),
        best_rmse=(
            float(training_run['best_rmse'])
            if training_run.get('best_rmse') is not None
            else None
        ),
        error_code=(
            str(training_run['error_code'])
            if training_run.get('error_code')
            else None
        ),
        summary=summary,
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

@router.patch(
    '/{model_id}/activate',
    operation_id='activate_model',
    response_model=ModelResult
)
async def activate_model(
    model_id: str,
    model_service: ModelServiceDep
) -> ModelResult:
    model = model_service.activate_model(model_id)

    if not model:
        raise HTTPException(status_code=404, detail='Model not found')

    return model

def _run_training_job(
    model_training_pipeline: ModelTrainingPipeline,
    training_run_id: str,
    parquet_path: str,
    optimize: bool,
    n_trials: int,
    activate_model: bool
) -> None:
    try:
        model_training_pipeline.train_model_from_parquet(
            training_run_id=training_run_id,
            parquet_path=Path(parquet_path),
            optimize=optimize,
            n_trials=n_trials,
            activate_model=activate_model
        )
    except Exception:
        return
