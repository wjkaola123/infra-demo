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