from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.dependencies import get_db, get_redis
from app.service.auth_service import AuthService
from app.handler.entity.request.auth import LoginRequest, RegisterRequest, RefreshRequest, LogoutRequest
from app.schemas.common import ApiResponse

router = APIRouter()


@router.post("/register", response_model=ApiResponse, status_code=201)
async def register(
    user_data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    service = AuthService(db, redis)
    try:
        token_data = await service.register(user_data.username, user_data.email, user_data.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiResponse(message="success", status=0, data=token_data)


@router.post("/login", response_model=ApiResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    service = AuthService(db, redis)
    try:
        token_data = await service.login(credentials.username, credentials.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    return ApiResponse(message="success", status=0, data=token_data)


@router.post("/refresh", response_model=ApiResponse)
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    service = AuthService(db, redis)
    try:
        token_data = await service.refresh_token(request.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    return ApiResponse(message="success", status=0, data=token_data)


@router.post("/logout", response_model=ApiResponse)
async def logout(
    request: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    service = AuthService(db, redis)
    await service.logout(request.refresh_token)
    return ApiResponse(message="success", status=0, data=None)