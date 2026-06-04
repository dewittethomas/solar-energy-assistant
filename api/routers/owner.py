from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from models.owner import OwnerPayload
from responses.owner_result import OwnerResult
from services.dependencies import get_owner_service
from services.owner_service import OwnerService

router = APIRouter(prefix='/owner', tags=['owner'])

OwnerServiceDep = Annotated[
    OwnerService,
    Depends(get_owner_service)
]


@router.get(
    '',
    operation_id='get_owner',
    response_model=OwnerResult
)
async def get_owner(
    owner_service: OwnerServiceDep
) -> OwnerResult:
    owner = owner_service.get_owner()

    if not owner:
        raise HTTPException(status_code=404, detail='Owner not found')

    return owner


@router.post(
    '',
    operation_id='create_owner',
    response_model=OwnerResult
)
async def create_owner(
    owner: OwnerPayload,
    owner_service: OwnerServiceDep
) -> OwnerResult:
    try:
        return owner_service.create_owner(owner)
    except ValueError as exc:
        message = str(exc)
        status_code = 409 if 'already exists' in message.lower() else 400
        raise HTTPException(status_code=status_code, detail=message)


@router.put(
    '',
    operation_id='update_owner',
    response_model=OwnerResult
)
async def update_owner(
    owner: OwnerPayload,
    owner_service: OwnerServiceDep
) -> OwnerResult:
    try:
        return owner_service.update_owner(owner)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
