from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis.asyncio import Redis

from app.dependencies import get_db, get_redis
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.schemas.common import ApiResponse

router = APIRouter()


@router.post("/", response_model=ApiResponse[UserResponse], status_code=201)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    cached = await redis.get(f"user:{user_data.username}")
    if cached:
        raise HTTPException(status_code=400, detail="Username already exists (cached)")

    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(**user_data.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await redis.set(f"user:{user.username}", user.email, ex=3600)

    return ApiResponse(data=user)


@router.get("/{user_id}", response_model=ApiResponse[UserResponse])
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return ApiResponse(data=user)
