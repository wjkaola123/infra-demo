from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.dependencies import get_db, get_redis
from app.service.user_service import UserService
from app.handler.entity.request.user import UserCreateRequest
from app.handler.entity.response.user import UserResponse
from app.schemas.common import ApiResponse

router = APIRouter()


@router.post("/", response_model=ApiResponse[UserResponse], status_code=201)
async def create_user(
    user_data: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
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
):
    service = UserService(db, redis)
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return ApiResponse(message="success", status=0, data=user)
