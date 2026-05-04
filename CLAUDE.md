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

**Roles API:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/roles/` | List roles (paginated, filterable by `name`), includes `assigned_users_count` per role |
| POST | `/api/v1/roles/` | Create role |
| GET | `/api/v1/roles/{id}` | Get role by ID |
| PUT | `/api/v1/roles/{id}` | Update role (name, description, and optionally permission_ids) |
| DELETE | `/api/v1/roles/{id}` | Delete role |
| PUT | `/api/v1/roles/{id}/permissions` | Replace all permissions for role |
| GET | `/api/v1/roles/permissions` | List all permissions |
| POST | `/api/v1/roles/{id}/permissions` | Assign permissions to role (additive) |
| GET | `/api/v1/roles/users/{user_id}/roles` | Get user's roles |
| POST | `/api/v1/roles/users/{user_id}/roles` | Assign role to user |
| DELETE | `/api/v1/roles/users/{user_id}/roles/{role_id}` | Remove role from user |
| GET | `/api/v1/roles/users/{user_id}/permissions` | Get user's permissions |


### Dependencies
- `app/dependencies.py` - `get_db()` for AsyncSession, `get_redis()` for Redis client, `get_current_user()` for auth, `require_permissions()` for RBAC
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
├── repository/                    # Data access layer
│   ├── entity/                    # Database entities (SQLAlchemy ORM Model)
│   │   ├── base.py               # Base + TimestampMixin
│   │   └── user.py               # User ORM Model
│   └── user_repository.py        # UserRepository data access class
├── entity/                        # Business entities (Domain Entity)
│   └── user.py                   # UserEntity
├── handler/                       # Request handling layer
│   └── entity/
│       ├── request/              # Request DTOs
│       │   ├── user.py          # UserCreateRequest, UserUpdateRequest
│       │   └── auth.py          # LoginRequest, RegisterRequest, RefreshRequest, LogoutRequest
│       └── response/
│           ├── user.py          # UserResponse
│           └── auth.py          # TokenResponse
├── service/                       # Business service layer
│   ├── user_service.py          # UserService
│   ├── auth_service.py          # AuthService (register/login/refresh/logout)
│   └── role_service.py          # RoleService (CRUD + RBAC)
├── api/                          # API routing layer
│   └── v1/endpoints/
│       ├── users.py             # User CRUD endpoints
│       ├── auth.py              # Auth endpoints (register/login/refresh/logout)
│       └── roles.py            # Roles/RBAC endpoints
├── tools/auth/                   # Auth utilities
│   ├── jwt.py                   # JWTHandler
│   └── hashing.py               # Password hashing
├── schemas/                      # Pydantic schemas
│   └── common.py                # ApiResponse
└── tasks/                        # Celery tasks
    └── example_tasks.py
```

**Layer responsibilities:**
- `repository/entity` - SQLAlchemy ORM models, corresponding to database table structures
- `repository` - Repository pattern, encapsulates database access logic
- `entity` - Business entities, business objects independent of the database
- `handler/entity/request` - External request DTOs, used for API input validation
- `handler/entity/response` - External response DTOs, used for API output formatting
- `service` - Business logic layer, orchestrates business operations
- `tools/auth` - Authentication utility functions

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