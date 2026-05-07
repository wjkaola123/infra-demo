# Activity Log Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现活动日志模块，记录 User/Role/Permission 的 CREATE/UPDATE/DELETE 操作

**Architecture:** 使用 SQLAlchemy 事件监听（after_insert, before_update/after_update, before_delete）自动捕获变更，通过 ContextVar 传递请求上下文

**Tech Stack:** SQLAlchemy async, PostgreSQL, FastAPI, ContextVar

---

## File Map

### Create
- `app/context.py` — AuditContext dataclass + ContextVar
- `app/repository/entity/activity_log.py` — ActivityLog ORM 模型
- `app/repository/activity_log_repository.py` — ActivityLogRepository
- `app/handler/entity/response/activity_log.py` — ActivityLogResponse DTO
- `app/api/v1/endpoints/activity_logs.py` — 日志查询 API
- `alembic/versions/005_add_activity_logs.py` — 迁移

### Modify
- `app/repository/entity/user.py` — 注册事件监听
- `app/repository/entity/role.py` — 注册事件监听
- `app/repository/entity/permission.py` — 注册事件监听
- `app/dependencies.py` — get_current_user 中设置 audit_context
- `app/api/v1/router.py` — 注册 activity_logs 路由

---

## Task 1: context.py — 审计上下文

**File:** Create: `app/context.py`

- [ ] **Step 1: Write the file**

```python
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional

@dataclass
class AuditContext:
    user_id: int
    username: str
    ip_address: Optional[str] = None

audit_context: ContextVar[AuditContext | None] = ContextVar("audit_context", default=None)
```

- [ ] **Step 2: Commit**

```bash
git add app/context.py && git commit -m "feat: add AuditContext for request-scoped audit user info"
```

---

## Task 2: ActivityLog ORM 模型

**File:** Create: `app/repository/entity/activity_log.py`

- [ ] **Step 1: Write the file**

```python
from sqlalchemy import Column, Integer, String, DateTime, JSON
from app.repository.entity.base import Base, TimestampMixin


class ActivityLog(Base, TimestampMixin):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_user_id = Column(Integer, nullable=False, index=True)
    actor_username = Column(String(50), nullable=False)
    action = Column(String(20), nullable=False, index=True)  # CREATE / UPDATE / DELETE
    resource_type = Column(String(20), nullable=False, index=True)  # user / role / permission
    resource_id = Column(Integer, nullable=False, index=True)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
```

- [ ] **Step 2: Commit**

```bash
git add app/repository/entity/activity_log.py && git commit -m "feat: add ActivityLog ORM model"
```

---

## Task 3: ActivityLogRepository

**File:** Create: `app/repository/activity_log_repository.py`

- [ ] **Step 1: Write the file**

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime
from app.repository.entity.activity_log import ActivityLog


class ActivityLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        actor_user_id: int,
        actor_username: str,
        action: str,
        resource_type: str,
        resource_id: int,
        old_value: dict | None,
        new_value: dict | None,
        ip_address: str | None,
    ) -> ActivityLog:
        log = ActivityLog(
            actor_user_id=actor_user_id,
            actor_username=actor_username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
        )
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def list_paginated(
        self,
        page: int,
        page_size: int,
        actor_user_id: int | None = None,
        resource_type: str | None = None,
        action: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> tuple[list[ActivityLog], int]:
        conditions = []
        if actor_user_id is not None:
            conditions.append(ActivityLog.actor_user_id == actor_user_id)
        if resource_type:
            conditions.append(ActivityLog.resource_type == resource_type)
        if action:
            conditions.append(ActivityLog.action == action)
        if start_date:
            conditions.append(ActivityLog.created_at >= start_date)
        if end_date:
            conditions.append(ActivityLog.created_at <= end_date)

        where_clause = and_(*conditions) if conditions else True

        count_result = await self.session.execute(
            select(func.count(ActivityLog.id)).where(where_clause)
        )
        total = count_result.scalar() or 0

        offset = (page - 1) * page_size
        result = await self.session.execute(
            select(ActivityLog)
            .where(where_clause)
            .order_by(ActivityLog.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all()), total
```

- [ ] **Step 2: Commit**

```bash
git add app/repository/activity_log_repository.py && git commit -m "feat: add ActivityLogRepository"
```

---

## Task 4: ActivityLogResponse DTO

**File:** Create: `app/handler/entity/response/activity_log.py`

- [ ] **Step 1: Write the file**

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ActivityLogResponse(BaseModel):
    id: int
    actor_user_id: int
    actor_username: str
    action: str
    resource_type: str
    resource_id: int
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedActivityLogResponse(BaseModel):
    items: list[ActivityLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
```

- [ ] **Step 2: Commit**

```bash
git add app/handler/entity/response/activity_log.py && git commit -m "feat: add ActivityLogResponse DTOs"
```

---

## Task 5: ActivityLogService + SQLAlchemy 事件监听工具

**File:** Create: `app/service/activity_log_service.py`

- [ ] **Step 1: Write the file**

```python
from sqlalchemy.orm import Mapper
from sqlalchemy.engine import Connection
from app.context import audit_context
from app.repository.activity_log_repository import ActivityLogRepository


def _resource_type_for_model(model_tablename: str) -> str:
    mapping = {
        "users": "user",
        "roles": "role",
        "permissions": "permission",
    }
    return mapping.get(model_tablename, model_tablename)


def _model_to_dict(model) -> dict:
    result = {}
    for column in model.__table__.columns:
        value = getattr(model, column.name)
        if hasattr(value, "to_dict"):
            result[column.name] = value.to_dict()
        elif hasattr(value, "__dict__"):
            pass
        else:
            result[column.name] = value
    return result


def _write_activity_log(
    connection: Connection,
    action: str,
    target,
    old_value: dict | None,
    new_value: dict | None,
) -> None:
    ctx = audit_context.get()
    if not ctx:
        return
    resource_type = _resource_type_for_model(target.__table__.name)
    resource_id = target.id
    connection.execute(
        ActivityLogRepository.__table__.insert().values(
            actor_user_id=ctx.user_id,
            actor_username=ctx.username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ctx.ip_address,
        )
    )


def receive_after_insert(mapper: Mapper, connection: Connection, target) -> None:
    _write_activity_log(connection, "CREATE", target, None, _model_to_dict(target))


def receive_before_update(mapper: Mapper, connection: Connection, target) -> None:
    target._audit_old_values = {c.name: getattr(target, c.name) for c in target.__table__.columns}


def receive_after_update(mapper: Mapper, connection: Connection, target) -> None:
    if not hasattr(target, "_audit_old_values"):
        return
    old_value = target._audit_old_values
    new_value = _model_to_dict(target)
    _write_activity_log(connection, "UPDATE", target, old_value, new_value)
    del target._audit_old_values


def receive_before_delete(mapper: Mapper, connection: Connection, target) -> None:
    _write_activity_log(connection, "DELETE", target, _model_to_dict(target), None)
```

> **Note:** The event listener functions need to use a direct SQL insert since they fire outside of the async session context. A simpler approach is to use `connection.execute` with raw SQL or a core-level insert. The above shows the pattern using `_write_activity_log`.

- [ ] **Step 2: Commit**

```bash
git add app/service/activity_log_service.py && git commit -m "feat: add ActivityLogService and SQLAlchemy event helpers"
```

---

## Task 6: 注册事件监听到 User 模型

**File:** Modify: `app/repository/entity/user.py`

- [ ] **Step 1: Add imports and event listeners at end of file**

Add after existing imports:
```python
from sqlalchemy import event
from app.service.activity_log_service import (
    receive_after_insert,
    receive_before_update,
    receive_after_update,
    receive_before_delete,
)
```

Add at end of file:
```python
event.listens_for(User, "after_insert")(receive_after_insert)
event.listens_for(User, "before_update")(receive_before_update)
event.listens_for(User, "after_update")(receive_after_update)
event.listens_for(User, "before_delete")(receive_before_delete)
```

- [ ] **Step 2: Commit**

```bash
git add app/repository/entity/user.py && git commit -m "feat: register audit events on User model"
```

---

## Task 7: 注册事件监听到 Role 模型

**File:** Modify: `app/repository/entity/role.py`

Same pattern as Task 6 — add imports and register events for Role and Permission models.

- [ ] **Step 1: Add imports**

```python
from sqlalchemy import event
from app.service.activity_log_service import (
    receive_after_insert,
    receive_before_update,
    receive_after_update,
    receive_before_delete,
)
```

- [ ] **Step 2: Register events at end of file**

```python
event.listens_for(Role, "after_insert")(receive_after_insert)
event.listens_for(Role, "before_update")(receive_before_update)
event.listens_for(Role, "after_update")(receive_after_update)
event.listens_for(Role, "before_delete")(receive_before_delete)
```

- [ ] **Step 3: Commit**

```bash
git add app/repository/entity/role.py && git commit -m "feat: register audit events on Role model"
```

---

## Task 8: 注册事件监听到 Permission 模型

**File:** Modify: `app/repository/entity/permission.py`

Same pattern as Task 7.

- [ ] **Step 1: Add imports**

```python
from sqlalchemy import event
from app.service.activity_log_service import (
    receive_after_insert,
    receive_before_update,
    receive_after_update,
    receive_before_delete,
)
```

- [ ] **Step 2: Register events at end of file**

```python
event.listens_for(Permission, "after_insert")(receive_after_insert)
event.listens_for(Permission, "before_update")(receive_before_update)
event.listens_for(Permission, "after_update")(receive_after_update)
event.listens_for(Permission, "before_delete")(receive_before_delete)
```

- [ ] **Step 3: Commit**

```bash
git add app/repository/entity/permission.py && git commit -m "feat: register audit events on Permission model"
```

---

## Task 9: 设置 AuditContext 于 get_current_user

**File:** Modify: `app/dependencies.py`

- [ ] **Step 1: Add import**

```python
from app.context import audit_context, AuditContext
```

- [ ] **Step 2: Modify get_current_user to set audit context**

Add inside `get_current_user`, after `if not user.is_active: raise HTTPException...` and before `return user`:

```python
from fastapi import Request
# Add Request parameter to get_current_user signature:
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    ...
    # Set audit context for SQLAlchemy event listeners
    ip_address = request.client.host if request.client else None
    audit_context.set(AuditContext(user_id=user.id, username=user.username, ip_address=ip_address))

    return user
```

> **Note:** Since `get_current_user` is a dependency used in every request, the audit context will be set automatically for all authenticated requests.

- [ ] **Step 3: Commit**

```bash
git add app/dependencies.py && git commit -m "feat: set AuditContext in get_current_user"
```

---

## Task 10: activity_logs API 端点

**File:** Create: `app/api/v1/endpoints/activity_logs.py`

- [ ] **Step 1: Write the file**

```python
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.dependencies import get_db, get_current_user
from app.repository.entity.user import User
from app.repository.activity_log_repository import ActivityLogRepository
from app.handler.entity.response.activity_log import ActivityLogResponse, PaginatedActivityLogResponse
from app.schemas.common import ApiResponse

router = APIRouter()


@router.get("/", response_model=ApiResponse[PaginatedActivityLogResponse])
async def list_activity_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=10000, description="Items per page"),
    actor_user_id: int | None = Query(None, description="Filter by actor user ID"),
    resource_type: str | None = Query(None, description="Filter by resource type: user, role, permission"),
    action: str | None = Query(None, description="Filter by action: CREATE, UPDATE, DELETE"),
    start_date: datetime | None = Query(None, description="Filter from date"),
    end_date: datetime | None = Query(None, description="Filter to date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = ActivityLogRepository(db)
    logs, total = await repo.list_paginated(
        page=page,
        page_size=page_size,
        actor_user_id=actor_user_id,
        resource_type=resource_type,
        action=action,
        start_date=start_date,
        end_date=end_date,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return ApiResponse(
        data=PaginatedActivityLogResponse(
            items=[ActivityLogResponse.model_validate(log) for log in logs],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )
```

- [ ] **Step 2: Commit**

```bash
git add app/api/v1/endpoints/activity_logs.py && git commit -m "feat: add activity_logs API endpoint"
```

---

## Task 11: 注册 activity_logs 路由

**File:** Modify: `app/api/v1/router.py`

- [ ] **Step 1: Add import**

```python
from app.api.v1.endpoints.activity_logs import router as activity_logs_router
```

- [ ] **Step 2: Register router**

```python
router.include_router(activity_logs_router, prefix="/activity-logs", tags=["activity-logs"])
```

- [ ] **Step 3: Commit**

```bash
git add app/api/v1/router.py && git commit -m "feat: register activity_logs router"
```

---

## Task 12: 数据库迁移

**File:** Create: `alembic/versions/005_add_activity_logs.py`

- [ ] **Step 1: Write the migration**

```python
"""add activity_logs table

Revision ID: 005
Revises: 004
Create Date: 2026-05-07
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'activity_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('actor_user_id', sa.Integer(), nullable=False),
        sa.Column('actor_username', sa.String(50), nullable=False),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('resource_type', sa.String(20), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=False),
        sa.Column('old_value', sa.JSON(), nullable=True),
        sa.Column('new_value', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_activity_logs_id', 'activity_logs', ['id'])
    op.create_index('ix_activity_logs_actor_user_id', 'activity_logs', ['actor_user_id'])
    op.create_index('ix_activity_logs_action', 'activity_logs', ['action'])
    op.create_index('ix_activity_logs_resource_type', 'activity_logs', ['resource_type'])
    op.create_index('ix_activity_logs_resource_id', 'activity_logs', ['resource_id'])


def downgrade() -> None:
    op.drop_table('activity_logs')
```

- [ ] **Step 2: Commit**

```bash
git add alembic/versions/005_add_activity_logs.py && git commit -m "feat: add activity_logs migration"
```

---

## Task 13: 验证

- [ ] **Step 1: 生成迁移 + 升级**

```bash
docker-compose exec api python -m alembic upgrade head
```

Expected: Migration 005 runs successfully, `activity_logs` table created.

- [ ] **Step 2: 创建/更新/删除资源，验证日志记录**

```bash
# 创建一个 user
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"username": "testlog1", "email": "testlog1@example.com"}'

# 查询日志
curl "http://localhost:8000/api/v1/activity-logs/?page=1&page_size=10" \
  -H "Authorization: Bearer <token>"
```

Expected: 日志列表包含 CREATE user 的记录，old_value / new_value 正确。

- [ ] **Step 3: 测试过滤条件**

```bash
# 按 resource_type 过滤
curl "http://localhost:8000/api/v1/activity-logs/?resource_type=user" \
  -H "Authorization: Bearer <token>"

# 按 action 过滤
curl "http://localhost:8000/api/v1/activity-logs/?action=CREATE" \
  -H "Authorization: Bearer <token>"
```

- [ ] **Step 4: 运行测试**

```bash
docker-compose exec api python -m pytest tests/ -v
```
