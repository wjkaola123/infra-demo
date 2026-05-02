from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from app.repository.user_repository import UserRepository
from app.handler.entity.request.user import UserCreateRequest, UserUpdateRequest
from app.handler.entity.response.user import UserResponse, PaginatedUserResponse


class UserService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.repo = UserRepository(db)
        self.redis = redis

    async def create_user(self, user_data: UserCreateRequest) -> UserResponse:
        cached = await self.redis.get(f"user:{user_data.username}")
        if cached:
            raise ValueError("Username already exists (cached)")

        existing = await self.repo.find_by_username(user_data.username)
        if existing:
            raise ValueError("Username already exists")

        user = await self.repo.create(user_data)
        await self.redis.set(f"user:{user.username}", user.email, ex=3600)

        return UserResponse.model_validate(user)

    async def get_user(self, user_id: int) -> UserResponse | None:
        user = await self.repo.find_by_id(user_id)
        if not user:
            return None
        return UserResponse.model_validate(user)

    async def list_users_paginated(self, page: int = 1, page_size: int = 10) -> PaginatedUserResponse:
        users, total = await self.repo.find_paginated(page, page_size)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return PaginatedUserResponse(
            items=[UserResponse.model_validate(u) for u in users],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update_user(self, user_id: int, user_data: UserUpdateRequest) -> UserResponse | None:
        user = await self.repo.find_by_id(user_id)
        if not user:
            return None

        if user_data.username is not None:
            existing = await self.repo.find_by_username(user_data.username)
            if existing and existing.id != user_id:
                raise ValueError("Username already exists")
            user.username = user_data.username

        if user_data.email is not None:
            user.email = user_data.email

        if user_data.is_active is not None:
            user.is_active = user_data.is_active

        updated = await self.repo.update(user)
        await self.redis.delete(f"user:{user.username}")
        return UserResponse.model_validate(updated)

    async def delete_user(self, user_id: int) -> bool:
        user = await self.repo.find_by_id(user_id)
        if not user:
            return False
        await self.redis.delete(f"user:{user.username}")
        await self.repo.delete(user)
        return True
