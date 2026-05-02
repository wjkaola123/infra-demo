from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.repository.entity.user import User
from app.tools.auth.hashing import verify_password, get_password_hash
from app.tools.auth.jwt import JWTHandler
from app.handler.entity.response.auth import TokenResponse


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

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

        return self._create_tokens(user.id)

    async def login(self, username: str, password: str) -> TokenResponse:
        result = await self.db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if not user or not user.password_hash:
            raise ValueError("Invalid credentials")

        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")

        if not user.is_active:
            raise ValueError("User is inactive")

        return self._create_tokens(user.id)

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        payload = JWTHandler.verify_token(refresh_token, expected_type="refresh")
        if not payload:
            raise ValueError("Invalid or expired refresh token")

        user_id = payload.get("sub")
        result = await self.db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        if not user.is_active:
            raise ValueError("User is inactive")

        return self._create_tokens(user.id)

    def _create_tokens(self, user_id: int) -> TokenResponse:
        access_token = JWTHandler.create_access_token({"sub": str(user_id)})
        refresh_token = JWTHandler.create_refresh_token({"sub": str(user_id)})
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)