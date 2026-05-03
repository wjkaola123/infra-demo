from typing import AsyncGenerator, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis.asyncio import Redis

from app.database import AsyncSessionLocal
from app.redis import redis_client
from app.repository.entity.user import User
from app.repository.entity.role import Role, Permission, user_roles, role_permissions
from app.tools.auth.jwt import JWTHandler


security = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_redis() -> Redis:
    return redis_client


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current user from JWT token."""
    token = credentials.credentials
    payload = JWTHandler.verify_token(token, expected_type="access")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if token is revoked (for refresh token revocation check)
    jti = payload.get("jti")
    if jti:
        redis = await get_redis()
        if await redis.exists(f"revoked:{jti}"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return user


def require_permissions(*required_permissions: str):
    """Dependency factory that returns a dependency to check permissions."""
    async def permission_checker(
        current_user: Annotated[User, Depends(get_current_user)],
        db: AsyncSession = Depends(get_db),
    ) -> User:
        # Get all permissions for the user through their roles
        query = (
            select(Permission.name)
            .join(role_permissions, role_permissions.c.permission_id == Permission.id)
            .join(Role, Role.id == role_permissions.c.role_id)
            .join(user_roles, user_roles.c.role_id == Role.id)
            .where(user_roles.c.user_id == current_user.id)
        )
        result = await db.execute(query)
        user_permissions = set(row[0] for row in result.fetchall())

        # Check if user has admin role (has all permissions)
        admin_query = (
            select(Role.id)
            .join(user_roles, user_roles.c.role_id == Role.id)
            .where(user_roles.c.user_id == current_user.id)
            .where(Role.name == "admin")
        )
        admin_result = await db.execute(admin_query)
        if admin_result.scalar_one_or_none():
            return current_user

        # Check if user has all required permissions
        # Flatten in case a list was passed as single arg
        perms = []
        for p in required_permissions:
            if isinstance(p, list):
                perms.extend(p)
            else:
                perms.append(p)

        missing = set(perms) - user_permissions
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(missing)}",
            )

        return current_user

    return permission_checker