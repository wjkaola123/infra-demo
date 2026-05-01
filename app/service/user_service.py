from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from app.repository.user_repository import UserRepository
from app.handler.entity.request.user import UserCreateRequest
from app.handler.entity.response.user import UserResponse


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
