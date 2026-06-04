from typing import Annotated

from fastapi import APIRouter, Depends

from repositories.metadata_repository import MetadataRepository
from services.dependencies import get_metadata_repository

router = APIRouter(prefix='/developer', tags=['developer'])

MetadataRepositoryDep = Annotated[
    MetadataRepository,
    Depends(get_metadata_repository)
]


@router.post('/reset-local-state', operation_id='reset_local_state')
async def reset_local_state(
    metadata_repository: MetadataRepositoryDep
) -> dict[str, object]:
    metadata_repository.reset_local_state()
    return {'status': 'ok'}


@router.delete('/owner', operation_id='delete_local_owner')
async def delete_local_owner(
    metadata_repository: MetadataRepositoryDep
) -> dict[str, object]:
    metadata_repository.delete_owner()
    return {'status': 'ok'}
