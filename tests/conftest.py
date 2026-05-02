import pytest
import pytest_asyncio
import socket
import os

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from redis.asyncio import Redis


def get_docker_host_ip() -> str:
    # In Docker container, use service names; on host, use localhost
    if os.environ.get('IN_DOCKER_CONTAINER'):
        return "host.docker.internal"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        host_ip = s.getsockname()[0]
        s.close()
        return host_ip
    except Exception:
        return "localhost"


# Use 'postgres' service name from docker-compose, not host IP
TEST_DATABASE_URL = "postgresql+asyncpg://app:app_password@postgres:5432/app_db"
TEST_REDIS_URL = "redis://redis:6379/0"


@pytest_asyncio.fixture
async def redis_client():
    """Create a redis client per test - each test gets its own connection."""
    client = Redis.from_url(TEST_REDIS_URL, decode_responses=True)
    yield client
    try:
        await client.aclose()
    except Exception:
        pass


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