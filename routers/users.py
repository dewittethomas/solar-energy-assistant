from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from models.user import UserCreate
from responses.user_result import UserResult
from services.dependencies import get_user_service
from services.user_service import UserService

router = APIRouter(prefix='/users', tags=['users'])

UserServiceDep = Annotated[
    UserService,
    Depends(get_user_service)
]

@router.get(
    '',
    operation_id='list_users',
    response_model=list[UserResult]
)
async def list_users(
    user_service: UserServiceDep
) -> list[UserResult]:
    return user_service.list_users()

@router.post(
    '',
    operation_id='create_user',
    response_model=UserResult
)
async def create_user(
    user: UserCreate,
    user_service: UserServiceDep
) -> UserResult:
    return user_service.create_user(user)

@router.get(
    '/{user_id}',
    operation_id='get_user',
    response_model=UserResult
)
async def get_user(
    user_id: str,
    user_service: UserServiceDep
) -> UserResult:
    user = user_service.get_user(user_id)

    if not user:
        raise HTTPException(status_code=404, detail='User not found')

    return user
