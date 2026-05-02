# FastAPI 后台服务框架搭建计划

## Context

构建一个完整的 FastAPI 后台服务框架，作为后续业务开发的基础。项目目录 `/home/wj/projects/infra-backend` 目前为空，需要从头搭建整个框架。

**核心要求：**
- FastAPI (最新版本) 作为 Web 框架
- Poetry 进行依赖管理
- PostgreSQL 数据库 (异步访问)
- Redis 缓存 (异步访问)
- Celery 分布式任务队列
- 全异步架构 (API + DB + Cache)

---

## 项目目录结构

```
infra-backend/
├── pyproject.toml              # Poetry 项目配置
├── poetry.lock                 # 锁定依赖版本
├── .env.example                # 环境变量示例
├── .env                        # 实际环境变量 (本地开发)
├── docker-compose.yml          # 本地开发服务 (PostgreSQL, Redis)
├── alembic.ini                 # 数据库迁移配置
├── alembic/                    # Alembic 迁移目录
│   ├── env.py
│   ├── script.mako
│   └── versions/
│       └── 001_initial.py
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理 (pydantic-settings)
│   ├── dependencies.py         # 依赖注入 (DB session, Redis)
│   ├── database.py             # 数据库引擎和 session factory
│   ├── redis.py                # Redis 连接池
│   ├── celery_app.py           # Celery 应用配置
│   ├── models/                 # SQLAlchemy ORM 模型
│   │   ├── __init__.py
│   │   └── base.py             # Base 模型类
│   │   └── user.py             # 示例用户模型
│   ├── schemas/                # Pydantic 请求/响应模型
│   │   ├── __init__.py
│   │   └── user.py             # 示例用户 schema
│   ├── api/                    # API 路由
│   │   ├── __init__.py
│   │   ├── router.py           # 主路由聚合
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── endpoints/
│   │       │   ├── __init__.py
│   │       │   └── users.py    # 示例用户 API
│   │       └── router.py       # v1 路由聚合
│   ├── services/               # 业务逻辑层
│   │   ├── __init__.py
│   │   └── user_service.py     # 示例用户服务
│   └── tasks/                  # Celery 任务
│       ├── __init__.py
│       └── example_tasks.py    # 示例后台任务
└── tests/                      # 测试目录
    ├── __init__.py
    ├── conftest.py             # 测试配置
    └── test_api/
        └── test_users.py
```

---

## 实施步骤

### Step 1: Poetry 项目初始化

创建 `pyproject.toml`：

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

执行: `poetry install`

---

### Step 2: Docker Compose 本地服务

创建 `docker-compose.yml`：

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

执行: `docker-compose up -d`

---

### Step 3: 配置管理 (pydantic-settings)

创建 `app/config.py`：

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

创建 `.env.example`：

```env
APP_NAME=infra-backend
DEBUG=false
DATABASE_URL=postgresql+asyncpg://app:app_password@localhost:5432/app_db
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

### Step 4: 数据库异步引擎

创建 `app/database.py`：

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

### Step 5: Redis 异步连接

创建 `app/redis.py`：

```python
from redis.asyncio import Redis, from_url

from app.config import settings


redis_client: Redis = from_url(settings.REDIS_URL, decode_responses=True)
```

---

### Step 6: 依赖注入

创建 `app/dependencies.py`：

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

### Step 7: 示例模型和 Schema

创建 `app/models/base.py`：

```python
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from app.database import Base


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

创建 `app/models/user.py`：

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

创建 `app/schemas/user.py`：

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

### Step 8: Celery 配置

创建 `app/celery_app.py`：

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

创建 `app/tasks/example_tasks.py`：

```python
import time
from app.celery_app import celery_app


@celery_app.task
def long_running_task(duration: int) -> str:
    time.sleep(duration)
    return f"Task completed after {duration} seconds"
```

---

### Step 9: API 路由结构

创建 `app/api/v1/endpoints/users.py`：

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

创建 `app/api/v1/router.py`：

```python
from fastapi import APIRouter
from app.api.v1.endpoints.users import router as users_router

router = APIRouter()
router.include_router(users_router, prefix="/users", tags=["users"])
```

创建 `app/api/router.py`：

```python
from fastapi import APIRouter
from app.api.v1.router import router as v1_router

router = APIRouter()
router.include_router(v1_router, prefix="/v1")
```

---

### Step 10: FastAPI 主入口 (Lifespan)

创建 `app/main.py`：

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

### Step 11: Alembic 数据库迁移

初始化 Alembic: `alembic init alembic`

修改 `alembic/env.py` 支持异步：

```python
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.config import settings
from app.models.base import Base  # 导入所有模型

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

创建初始迁移: `alembic revision --autogenerate -m "initial"`
应用迁移: `alembic upgrade head`

---

## 验证步骤

1. **启动基础服务:**
   ```bash
   docker-compose up -d
   ```

2. **安装依赖:**
   ```bash
   poetry install
   ```

3. **应用数据库迁移:**
   ```bash
   alembic upgrade head
   ```

4. **启动 FastAPI:**
   ```bash
   poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **验证 API:**
   - 访问 http://localhost:8000/docs 查看 Swagger UI
   - 访问 http://localhost:8000/health 验证健康检查
   - POST http://localhost:8000/api/v1/users 创建用户
   - GET http://localhost:8000/api/v1/users/{id} 获取用户

6. **启动 Celery Worker:**
   ```bash
   poetry run celery -A app.celery_app worker --loglevel=info
   ```

7. **验证 Celery 任务:**
   ```python
   from app.tasks.example_tasks import long_running_task
   result = long_running_task.delay(5)
   print(result.get())  # 等待结果
   ```

---

## 关键文件清单

| 文件 | 用途 |
|------|------|
| `pyproject.toml` | Poetry 依赖管理 |
| `docker-compose.yml` | PostgreSQL + Redis 服务 |
| `app/config.py` | pydantic-settings 配置 |
| `app/database.py` | SQLAlchemy async engine |
| `app/redis.py` | Redis async client |
| `app/dependencies.py` | FastAPI 依赖注入 |
| `app/main.py` | FastAPI 入口 + lifespan |
| `app/celery_app.py` | Celery 配置 |
| `alembic/env.py` | 异步迁移支持 |

---

## 注意事项

1. **异步一致性:** 所有 DB 操作使用 `AsyncSession`，Redis 使用 `redis.asyncio.Redis`
2. **Lifespan 管理:** 使用 `@asynccontextmanager` 统一管理资源生命周期
3. **依赖注入:** 通过 `Depends()` 提供 session 和 redis client，确保请求级隔离
4. **Celery 与 FastAPI 分离:** Celery worker 作为独立进程运行，共享配置模块