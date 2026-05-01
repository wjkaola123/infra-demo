# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI backend service framework with full async architecture (API + PostgreSQL + Redis + Celery).

## Common Commands

```bash
# Start infrastructure services (PostgreSQL, Redis)
docker-compose up -d

# Apply database migrations
alembic upgrade head

# Start development server with hot reload
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
poetry run pytest

# Run a single test
poetry run pytest tests/test_api/test_users.py -v

# Start Celery worker
poetry run celery -A app.celery_app worker --loglevel=info
```

## Architecture

### Configuration
- `app/config.py` - pydantic-settings based configuration, loaded from `.env`
- `settings.DEBUG` flag controls logging middleware behavior

### Request Flow
```
Client → LoggingMiddleware (captures request/response in DEBUG mode) → API Router → Endpoint

API Router hierarchy:
  app/api/router.py (prefix: /api)
    └── app/api/v1/router.py (prefix: /v1)
          └── app/api/v1/endpoints/users.py
```

### Response Format
All API responses use `ApiResponse[T]` from `app/schemas/common.py`:
- `message: str = "success"`
- `status: int = 0`
- `data: T | None = None`

### Middleware
- `app/middleware/logging.py` - ASGI middleware capturing method, URL, status, process_time, request_body, response_body
- Only active when `settings.DEBUG = true`

### Dependencies
- `app/dependencies.py` - `get_db()` for AsyncSession, `get_redis()` for Redis client
- Injected via FastAPI `Depends()`

### Data Layer
- SQLAlchemy async with `asyncpg` driver
- Alembic for migrations (async support configured in `alembic/env.py`)
- Redis async client for caching

## Code Push

Use GitHub MCP (`mcp__plugin_github_github__push_files`) instead of git push to avoid SSH issues.

## DDD Directory Structure

Follow Domain-Driven Design principles for code organization:

```
app/
├── repository/                    # 数据访问层
│   ├── entity/                    # 数据库实体（SQLAlchemy ORM Model）
│   │   ├── base.py               # Base + TimestampMixin
│   │   └── user.py               # User ORM Model
│   └── user_repository.py        # UserRepository 数据访问类
├── entity/                        # 业务实体（Domain Entity）
│   └── user.py                   # UserEntity
├── handler/                       # 请求处理层
│   └── entity/
│       ├── request/              # 请求 DTO
│       │   └── user.py          # UserCreateRequest
│       └── response/            # 响应 DTO
│           └── user.py          # UserResponse
├── service/                       # 业务服务层
│   └── user_service.py          # UserService
├── api/                          # API 路由层
│   └── v1/endpoints/users.py    # 用户 API 端点
├── middleware/                   # 中间件
│   └── logging.py
└── tasks/                        # Celery 任务
```

**Layer responsibilities:**
- `repository/entity` - SQLAlchemy ORM 模型，对应数据库表结构
- `repository` - Repository 模式，封装数据库访问逻辑
- `entity` - 业务实体，独立于数据库的业务对象
- `handler/entity/request` - 外部请求 DTO，用于 API 输入验证
- `handler/entity/response` - 外部响应 DTO，用于 API 输出格式化
- `service` - 业务逻辑层，编排业务操作

## File Structure

```
app/
├── main.py              # FastAPI app + lifespan
├── config.py             # Settings
├── dependencies.py       # DI (get_db, get_redis)
├── database.py           # SQLAlchemy async engine
├── redis.py              # Redis async client
├── celery_app.py         # Celery config
├── models/               # SQLAlchemy models
├── schemas/              # Pydantic schemas (common.py has ApiResponse)
├── api/                  # Route handlers
├── services/             # Business logic
└── middleware/           # ASGI middleware (logging)
```