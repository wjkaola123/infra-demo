from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.repository.entity.user import User
from app.entity.user import UserEntity


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_username(self, username: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def find_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.id == user_id).options(selectinload(User.roles))
        )
        return result.scalar_one_or_none()

    async def create(self, user_entity: UserEntity) -> User:
        user = User(
            username=user_entity.username,
            email=user_entity.email,
            is_active=user_entity.is_active,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def find_all(self) -> list[User]:
        result = await self.session.execute(select(User))
        return list(result.scalars().all())

    async def find_paginated(self, page: int, page_size: int) -> tuple[list[User], int]:
        from sqlalchemy import func
        offset = (page - 1) * page_size
        count_result = await self.session.execute(select(func.count(User.id)))
        total = count_result.scalar() or 0
        result = await self.session.execute(
            select(User).offset(offset).limit(page_size).options(selectinload(User.roles))
        )
        return list(result.scalars().all()), total

    async def update(self, user: User) -> User:
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.commit()
