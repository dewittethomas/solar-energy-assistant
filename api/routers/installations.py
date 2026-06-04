from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from models.installation import InstallationCreate
from models.installation_configuration import (
    ConsumingActivity,
    InstallationConfigurationUpdate,
)
from responses.dashboard_result import DashboardResult
from responses.installation_configuration_result import (
    InstallationConfigurationResult,
)
from responses.prediction_not_ready_result import PredictionNotReadyResult
from responses.prediction_result import PredictionResult
from services.dependencies import get_installation_service
from services.installation_service import InstallationService
from services.prediction_service import ModelNotReadyError

router = APIRouter(prefix='/installations', tags=['installations'])

InstallationServiceDep = Annotated[
    InstallationService,
    Depends(get_installation_service)
]


@router.post(
    '',
    operation_id='create_installation',
    response_model=InstallationConfigurationResult
)
async def create_installation(
    installation: InstallationCreate,
    installation_service: InstallationServiceDep
) -> InstallationConfigurationResult:
    try:
        return installation_service.create_installation(installation)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get(
    '/active',
    operation_id='get_active_installation',
    response_model=InstallationConfigurationResult
)
async def get_active_installation(
    installation_service: InstallationServiceDep
) -> InstallationConfigurationResult:
    try:
        return installation_service.get_active_configuration()
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get(
    '/{installation_id}/configuration',
    operation_id='get_installation_configuration',
    response_model=InstallationConfigurationResult
)
async def get_configuration(
    installation_id: str,
    installation_service: InstallationServiceDep
) -> InstallationConfigurationResult:
    return installation_service.get_configuration(installation_id)


@router.put(
    '/{installation_id}/configuration',
    operation_id='save_installation_configuration',
    response_model=InstallationConfigurationResult
)
async def save_configuration(
    installation_id: str,
    configuration: InstallationConfigurationUpdate,
    installation_service: InstallationServiceDep
) -> InstallationConfigurationResult:
    return installation_service.save_configuration(
        installation_id,
        configuration
    )


@router.get(
    '/consuming-activities/defaults',
    operation_id='list_default_consuming_activities',
    response_model=list[ConsumingActivity]
)
async def list_default_consuming_activities(
    installation_service: InstallationServiceDep
) -> list[ConsumingActivity]:
    return [
        ConsumingActivity.model_validate(activity)
        for activity in installation_service.list_available_consuming_activities()
    ]


@router.post(
    '/{installation_id}/seed-default-consuming-activities',
    operation_id='seed_default_consuming_activities',
    response_model=InstallationConfigurationResult
)
async def seed_default_consuming_activities(
    installation_id: str,
    installation_service: InstallationServiceDep
) -> InstallationConfigurationResult:
    return InstallationConfigurationResult.model_validate(
        installation_service.seed_default_consuming_activities(installation_id)
    )


@router.get(
    '/{installation_id}/dashboard',
    operation_id='get_installation_dashboard',
    response_model=DashboardResult
)
async def get_dashboard(
    installation_id: str,
    installation_service: InstallationServiceDep
) -> DashboardResult:
    return installation_service.get_dashboard(installation_id)


@router.get(
    '/{installation_id}/predictions',
    operation_id='predict_installation_solar_yield',
    response_model=PredictionResult | PredictionNotReadyResult
)
async def predict_installation_solar_yield(
    installation_id: str,
    installation_service: InstallationServiceDep,
    start_date: str = Query(...),
    end_date: str = Query(...)
) -> PredictionResult:
    try:
        return installation_service.predict(
            installation_id,
            start_date,
            end_date
        )
    except ModelNotReadyError as e:
        return PredictionNotReadyResult(
            status='not_ready',
            reason='model_training_in_progress',
            training_run_id=e.training_run_id
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Prediction failed: {str(e)}')
