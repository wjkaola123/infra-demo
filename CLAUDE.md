# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI backend service framework with full async architecture (API + PostgreSQL + Redis + Celery).

## Common Commands

```bash
# Start all services (PostgreSQL, Redis, API, Celery)
docker-compose up -d

# Rebuild and start all services
docker-compose up -d --build

# Stop all services
docker-compose down

# Apply database migrations
docker-compose exec api python -m alembic upgrade head

# Run tests (in Docker container)
docker-compose exec api python -m pytest tests/ -v

# Run tests locally
poetry run pytest tests/ -v
```

## Architecture

### Configuration
- `app/config.py` - pydantic-settings based configuration, loaded from `.env`

### Request Flow
```
Client → CORS Middleware → API Router → Endpoint

API Router hierarchy:
  app/api/router.py (prefix: /api)
    └── app/api/v1/router.py (prefix: /v1)
          └── app/api/v1/endpoints/{users,auth}.py
```

### Response Format
All API responses use `ApiResponse[T]` from `app/schemas/common.py`:
- `message: str = "success"`
- `status: int = 0`
- `data: T | None = None`

### API Endpoints

**Health & Users:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/users/` | List all users |
| POST | `/api/v1/users/` | Create a new user |
| GET | `/api/v1/users/{id}` | Get user by ID |
| PUT | `/api/v1/users/{id}` | Update user by ID |
| DELETE | `/api/v1/users/{id}` | Delete user by ID |

**Authentication:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | User login |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Revoke refresh token |

### Dependencies
- `app/dependencies.py` - `get_db()` for AsyncSession, `get_redis()` for Redis client
- Injected via FastAPI `Depends()`

### Data Layer
- SQLAlchemy async with `asyncpg` driver
- Alembic for migrations (async support configured in `alembic/env.py`)
- Redis async client for caching and token revocation

## Authentication Module

### Token Structure
- **Access token**: 30 min expiry, contains `sub` (user ID), `type: "access"`
- **Refresh token**: 7 days expiry, contains `sub`, `type: "refresh"`, `jti` (JWT ID)

### Redis Key Patterns
- `revoked:{jti}` - Revoked token blacklist (7 day TTL)
- `refresh:{user_id}:{jti}` - Token tracking (7 day TTL)

### Logout Flow
1. Client sends refresh_token to `/api/v1/auth/logout`
2. Server extracts `jti` from token
3. Server adds `jti` to Redis blacklist
4. Subsequent refresh attempts with this token fail with 401

### Auth Service Location
- `app/tools/auth/jwt.py` - JWT creation/verification
- `app/tools/auth/hashing.py` - Password hashing (bcrypt)
- `app/service/auth_service.py` - Business logic

## DDD Directory Structure

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
│       │   ├── user.py          # UserCreateRequest, UserUpdateRequest
│       │   └── auth.py          # LoginRequest, RegisterRequest, RefreshRequest, LogoutRequest
│       └── response/
│           ├── user.py          # UserResponse
│           └── auth.py          # TokenResponse
├── service/                       # 业务服务层
│   ├── user_service.py          # UserService
│   └── auth_service.py          # AuthService (register/login/refresh/logout)
├── api/                          # API 路由层
│   └── v1/endpoints/
│       ├── users.py             # User CRUD endpoints
│       └── auth.py             # Auth endpoints (register/login/refresh/logout)
├── tools/auth/                   # Auth utilities
│   ├── jwt.py                   # JWTHandler
│   └── hashing.py               # Password hashing
├── schemas/                      # Pydantic schemas
│   └── common.py                # ApiResponse
└── tasks/                        # Celery tasks
    └── example_tasks.py
```

**Layer responsibilities:**
- `repository/entity` - SQLAlchemy ORM 模型，对应数据库表结构
- `repository` - Repository 模式，封装数据库访问逻辑
- `entity` - 业务实体，独立于数据库的业务对象
- `handler/entity/request` - 外部请求 DTO，用于 API 输入验证
- `handler/entity/response` - 外部响应 DTO，用于 API 输出格式化
- `service` - 业务逻辑层，编排业务操作
- `tools/auth` - 认证工具函数

## File Structure

```
app/
├── main.py              # FastAPI app + lifespan
├── config.py            # Settings
├── dependencies.py      # DI (get_db, get_redis)
├── database.py          # SQLAlchemy async engine
├── redis.py             # Redis async client
├── celery_app.py        # Celery config
├── api/                 # Route handlers
├── service/             # Business logic
├── repository/          # Data access layer
├── entity/              # Domain entities
├── handler/             # Request/Response DTOs
├── tools/auth/          # Auth utilities (jwt, hashing)
├── schemas/             # Pydantic schemas (common.py has ApiResponse)
└── tasks/               # Celery tasks
```

## Local Development (without Docker)

```bash
# Start PostgreSQL and Redis locally, then:
poetry install
poetry run alembic upgrade head

# Run API (in one terminal):
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run Celery worker (in another terminal):
poetry run celery -A app.celery_app worker --loglevel=info
```

## Code Push

Use GitHub MCP (`mcp__plugin_github_github__push_files`) instead of git push to avoid SSH issues.