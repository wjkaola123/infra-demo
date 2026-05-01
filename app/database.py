from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.config import settings
from app.repository.entity.base import Base


engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)
