# FastAPI Backend Service Framework Plan

## Context

Build a complete FastAPI backend service framework as the foundation for subsequent business development. Project directory `/home/wj/projects/infra-backend` is currently empty, need to build the entire framework from scratch.

**Core Requirements:**
- FastAPI (latest version) as web framework
- Poetry for dependency management
- PostgreSQL database (async access)
- Redis cache (async access)
- Celery distributed task queue
- Full async architecture (API + DB + Cache)

---

## Project Directory Structure

```
infra-backend/
├── pyproject.toml              # Poetry project config
├── poetry.lock                 # Locked dependency versions
├── .env.example                # Environment variable example
├── .env                        # Actual environment variables (local development)
├── docker-compose.yml          # Local development services (PostgreSQL, Redis)
├── alembic.ini                 # Database migration config
├── alembic/                    # Alembic migration directory
│   ├── env.py
│   ├── script.mako
│   └── versions/
│       └── 001_initial.py
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry
│   ├── config.py               # Configuration management (pydantic-settings)
│   ├── dependencies.py         # Dependency injection (DB session, Redis)
│   ├── database.py             # Database engine and session factory
│   ├── redis.py                # Redis connection pool
│   ├── celery_app.py           # Celery application config
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   └── base.py             # Base model class
│   │   └── user.py             # Sample user model
│   ├── schemas/                # Pydantic request/response models
│   │   ├── __init__.py
│   │   └── user.py             # Sample user schema
│   ├── api/                    # API routes
│   │   ├── __init__.py
│   │   ├── router.py           # Main route aggregation
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── endpoints/
│   │       │   ├── __init__.py
│   │       │   └── users.py    # Sample user API
│   │       └── router.py       # v1 route aggregation
│   ├── services/               # Business logic layer
│   │   ├── __init__.py
│   │   └── user_service.py     # Sample user service
│   └── tasks/                  # Celery tasks
│       ├── __init__.py
│       └── example_tasks.py    # Sample background tasks
└── tests/                      # Test directory
    ├── __init__.py
    ├── conftest.py             # Test configuration
    └── test_api/
        └── test_users.py
```

---

## Implementation Steps

### Step 1: Poetry Project Initialization

Create `pyproject.toml`:

```toml
[tool.poetry]
name = "infra-backend"
version = "0.1.0"
description = "FastAPI backend service framework"
authors = ["wj"]
readme = "README.md"
package-mode = false

[tool.poetry.dependencies]
python = "^3.13"
fastapi = "0.136.1"
uvicorn = {extras = ["standard"], version = "^0.30.0"}
sqlalchemy = "^2.0.0"
asyncpg = "^0.30.0"
alembic = "^1.13.0"
redis = {extras = ["hiredis"], version = "^5.0.0"}
celery = {extras = ["redis"], version = "^5.4.0"}
pydantic-settings = "^2.5.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-asyncio = "^0.23.0"
httpx = "^0.27.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

Run: `poetry install`

---

### Step 2: Docker Compose Local Services

Create `docker-compose.yml`:

```yaml
version: "3.8"
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app_password
      POSTGRES_DB: app_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

Run: `docker-compose up -d`

---

### Step 3: Configuration Management (pydantic-settings)

Create `app/config.py`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App
    APP_NAME: str = "infra-backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://app:app_password@localhost:5432/app_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"


settings = Settings()
```

Create `.env.example`:

```env
APP_NAME=infra-backend
DEBUG=false
DATABASE_URL=postgresql+asyncpg://app:app_password@localhost:5432/app_db
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

### Step 4: Database Async Engine

Create `app/database.py`:

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass
```

---

### Step 5: Redis Async Connection

Create `app/redis.py`:

```python
from redis.asyncio import Redis, from_url

from app.config import settings


redis_client: Redis = from_url(settings.REDIS_URL, decode_responses=True)
```

---

### Step 6: Dependency Injection

Create `app/dependencies.py`:

```python
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.database import AsyncSessionLocal
from app.redis import redis_client


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_redis() -> Redis:
    return redis_client
```

---

### Step 7: Sample Models and Schemas

Create `app/models/base.py`:

```python
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from app.database import Base


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

Create `app/models/user.py`:

```python
from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base
from app.models.base import TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
```

Create `app/schemas/user.py`:

```python
from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    email: EmailStr


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
```

---

### Step 8: Celery Configuration

Create `app/celery_app.py`:

```python
from celery import Celery

from app.config import settings


celery_app = Celery(
    "infra-backend",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.example_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
```

Create `app/tasks/example_tasks.py`:

```python
import time
from app.celery_app import celery_app


@celery_app.task
def long_running_task(duration: int) -> str:
    time.sleep(duration)
    return f"Task completed after {duration} seconds"
```

---

### Step 9: API Route Structure

Create `app/api/v1/endpoints/users.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis.asyncio import Redis

from app.dependencies import get_db, get_redis
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    # Check cache first
    cached = await redis.get(f"user:{user_data.username}")
    if cached:
        raise HTTPException(status_code=400, detail="Username already exists (cached)")

    # Check database
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(**user_data.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Cache the user
    await redis.set(f"user:{user.username}", user.email, ex=3600)

    return user


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

Create `app/api/v1/router.py`:

```python
from fastapi import APIRouter
from app.api.v1.endpoints.users import router as users_router

router = APIRouter()
router.include_router(users_router, prefix="/users", tags=["users"])
```

Create `app/api/router.py`:

```python
from fastapi import APIRouter
from app.api.v1.router import router as v1_router

router = APIRouter()
router.include_router(v1_router, prefix="/v1")
```

---

### Step 10: FastAPI Main Entry (Lifespan)

Create `app/main.py`:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.redis import redis_client
from app.api.router import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify connections
    async with engine.begin() as conn:
        # Optional: create tables if not using Alembic
        pass

    await redis_client.ping()

    yield

    # Shutdown: cleanup
    await engine.dispose()
    await redis_client.aclose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}
```

---

### Step 11: Alembic Database Migration

Initialize Alembic: `alembic init alembic`

Modify `alembic/env.py` to support async:

```python
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.config import settings
from app.models.base import Base  # Import all models

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    import asyncio
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

Create initial migration: `alembic revision --autogenerate -m "initial"`
Apply migration: `alembic upgrade head`

---

## Verification Steps

1. **Start base services:**
   ```bash
   docker-compose up -d
   ```

2. **Install dependencies:**
   ```bash
   poetry install
   ```

3. **Apply database migrations:**
   ```bash
   alembic upgrade head
   ```

4. **Start FastAPI:**
   ```bash
   poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Verify API:**
   - Visit http://localhost:8000/docs to view Swagger UI
   - Visit http://localhost:8000/health to verify health check
   - POST http://localhost:8000/api/v1/users to create user
   - GET http://localhost:8000/api/v1/users/{id} to get user

6. **Start Celery Worker:**
   ```bash
   poetry run celery -A app.celery_app worker --loglevel=info
   ```

7. **Verify Celery tasks:**
   ```python
   from app.tasks.example_tasks import long_running_task
   result = long_running_task.delay(5)
   print(result.get())  # Wait for result
   ```

---

## Key Files List

| File | Purpose |
|------|---------|
| `pyproject.toml` | Poetry dependency management |
| `docker-compose.yml` | PostgreSQL + Redis services |
| `app/config.py` | pydantic-settings configuration |
| `app/database.py` | SQLAlchemy async engine |
| `app/redis.py` | Redis async client |
| `app/dependencies.py` | FastAPI dependency injection |
| `app/main.py` | FastAPI entry + lifespan |
| `app/celery_app.py` | Celery configuration |
| `alembic/env.py` | Async migration support |

---

## Notes

1. **Async consistency:** All DB operations use `AsyncSession`, Redis uses `redis.asyncio.Redis`
2. **Lifespan management:** Use `@asynccontextmanager` to uniformly manage resource lifecycle
3. **Dependency injection:** Provide session and redis client through `Depends()`, ensuring request-level isolation
4. **Celery and FastAPI separation:** Celery worker runs as an independent process, sharing configuration module