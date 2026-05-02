import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from redis.asyncio import Redis

from app.config import settings


TEST_DATABASE_URL = "postgresql+asyncpg://app:app_password@localhost:5432/app_db"


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    TestAsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with TestAsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def redis_client():
    """Create a redis client per test - each test gets its own connection."""
    client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    yield client
    try:
        await client.aclose()
    except Exception:
        pass


@pytest_asyncio.fixture
async def client(redis_client):
    """Create a test client."""
    from app.main import app
    from app.dependencies import get_db, get_redis

    async def override_get_db():
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        TestAsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        async with TestAsyncSessionLocal() as session:
            yield session

    async def override_get_redis():
        return redis_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()