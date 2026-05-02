from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.repository.entity.user import User
from app.tools.auth.hashing import verify_password, get_password_hash
from app.tools.auth.jwt import JWTHandler
from app.handler.entity.response.auth import TokenResponse


class AuthService:
    def __init__(self, db: AsyncSession, redis_client=None):
        self.db = db
        self._redis = redis_client

    async def _get_redis(self):
        if self._redis is None:
            from app.redis import redis_client
            return redis_client
        return self._redis

    async def register(self, username: str, email: str, password: str) -> TokenResponse:
        result = await self.db.execute(select(User).where(User.username == username))
        if result.scalar_one_or_none():
            raise ValueError("Username already exists")

        result = await self.db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise ValueError("Email already exists")

        user = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return await self._create_tokens(user.id)

    async def login(self, username: str, password: str) -> TokenResponse:
        result = await self.db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if not user or not user.password_hash:
            raise ValueError("Invalid credentials")

        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")

        if not user.is_active:
            raise ValueError("User is inactive")

        return await self._create_tokens(user.id)

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        payload = JWTHandler.verify_token(refresh_token, expected_type="refresh")
        if not payload:
            raise ValueError("Invalid or expired refresh token")

        jti = payload.get("jti")
        redis = await self._get_redis()
        if jti and await redis.exists(f"revoked:{jti}"):
            raise ValueError("Token has been revoked")

        user_id = payload.get("sub")
        result = await self.db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        if not user.is_active:
            raise ValueError("User is inactive")

        return await self._create_tokens(user.id)

    async def logout(self, refresh_token: str) -> None:
        payload = JWTHandler.decode_token(refresh_token)
        if payload:
            jti = payload.get("jti")
            if jti:
                redis = await self._get_redis()
                await redis.setex(f"revoked:{jti}", 7 * 24 * 3600, "1")

    async def _create_tokens(self, user_id: int) -> TokenResponse:
        access_token = JWTHandler.create_access_token({"sub": str(user_id)})
        refresh_token, jti = JWTHandler.create_refresh_token({"sub": str(user_id)})
        redis = await self._get_redis()
        await redis.setex(f"refresh:{user_id}:{jti}", 7 * 24 * 3600, "1")
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)