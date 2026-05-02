from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.dependencies import get_db, get_redis, get_current_user, require_permissions
from app.service.user_service import UserService
from app.handler.entity.request.user import UserCreateRequest, UserUpdateRequest
from app.handler.entity.response.user import UserResponse
from app.repository.entity.user import User
from app.schemas.common import ApiResponse

router = APIRouter()


@router.get("/", response_model=ApiResponse[list[UserResponse]])
async def list_users(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(require_permissions("users:read")),
):
    service = UserService(db, redis)
    users = await service.list_users()
    return ApiResponse(message="success", status=0, data=users)


@router.post("/", response_model=ApiResponse[UserResponse], status_code=201)
async def create_user(
    user_data: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(require_permissions("users:write")),
):
    service = UserService(db, redis)
    try:
        user = await service.create_user(user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiResponse(message="success", status=0, data=user)


@router.get("/{user_id}", response_model=ApiResponse[UserResponse])
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(require_permissions("users:read")),
):
    service = UserService(db, redis)
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return ApiResponse(message="success", status=0, data=user)


@router.put("/{user_id}", response_model=ApiResponse[UserResponse])
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(require_permissions("users:write")),
):
    service = UserService(db, redis)
    try:
        user = await service.update_user(user_id, user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return ApiResponse(message="success", status=0, data=user)


@router.delete("/{user_id}", response_model=ApiResponse[dict])
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(require_permissions("users:delete")),
):
    service = UserService(db, redis)
    deleted = await service.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return ApiResponse(message="success", status=0, data={"id": user_id})