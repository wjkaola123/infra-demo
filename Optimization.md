# FastAPI 项目 DDD 架构优化方案

## Context

当前项目结构较为扁平，所有代码混在 `models/`、`schemas/`、`api/endpoints/` 目录下，不利于后续业务扩展。需要按照 DDD（领域驱动设计）思路重新组织目录结构，使代码职责更清晰。

**用户要求的新目录结构：**
- `app/repository/entity` - 数据库 Model 实体类（SQLAlchemy ORM 模型）
- `app/repository` - 数据访问类（Repository 模式）
- `app/entity` - 业务对象实体类（Domain Entity）
- `app/handler/entity/request` - 外部请求 DTO
- `app/handler/entity/response` - 外部响应 DTO

---

## 目标目录结构

```
app/
├── main.py                      # FastAPI 入口
├── config.py                     # 配置
├── dependencies.py              # 依赖注入
├── database.py                   # 数据库引擎
├── redis.py                     # Redis 客户端
├── celery_app.py                # Celery 配置
│
├── repository/                  # 数据访问层
│   ├── __init__.py
│   ├── entity/                  # 数据库实体（ORM Model）
│   │   ├── __init__.py
│   │   ├── base.py             # Base + TimestampMixin
│   │   └── user.py             # User ORM Model
│   └── user_repository.py      # UserRepository 类
│
├── entity/                      # 业务实体层（Domain Entity）
│   ├── __init__.py
│   └── user.py                  # User 业务实体（可选，如有业务逻辑）
│
├── handler/                     # 请求处理层
│   ├── __init__.py
│   └── entity/                  # 请求/响应 DTO
│       ├── __init__.py
│       ├── request/            # 请求 DTO
│       │   ├── __init__.py
│       │   └── user.py         # UserCreateRequest
│       └── response/           # 响应 DTO
│           ├── __init__.py
│           └── user.py         # UserResponse
│
├── service/                    # 业务服务层
│   ├── __init__.py
│   └── user_service.py         # 用户业务逻辑
│
├── api/                        # API 路由层
│   ├── __init__.py
│   ├── router.py
│   └── v1/
│       ├── __init__.py
│       ├── router.py
│       └── endpoints/
│           ├── __init__.py
│           └── users.py        # 用户 API 端点
│
├── middleware/                 # 中间件
│   ├── __init__.py
│   └── logging.py
│
└── tasks/                      # Celery 任务
    ├── __init__.py
    └── example_tasks.py
```

---

## 实施步骤

### Step 1: 创建新目录结构

```bash
mkdir -p app/repository/entity
mkdir -p app/entity
mkdir -p app/handler/entity/request
mkdir -p app/handler/entity/response
mkdir -p app/service
```

### Step 2: 迁移数据库实体（ORM Model）

**From:** `app/models/user.py`, `app/models/base.py`
**To:** `app/repository/entity/user.py`, `app/repository/entity/base.py`

- `Base` → `app/repository/entity/base.py`
- `TimestampMixin` → `app/repository/entity/base.py`
- `User` → `app/repository/entity/user.py`

### Step 3: 创建 UserRepository 数据访问类

**File:** `app/repository/user_repository.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repository.entity.user import User
from app.handler.entity.request.user import UserCreateRequest

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_username(self, username: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def find_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_data: UserCreateRequest) -> User:
        user = User(**user_data.model_dump())
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
```

### Step 4: 创建业务实体（Domain Entity）

**File:** `app/entity/user.py`

业务实体与数据库实体分离，如果后续有复杂业务逻辑可在此类中添加。

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class UserEntity:
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
```

### Step 5: 创建请求/响应 DTO

**Request:** `app/handler/entity/request/user.py`

```python
from pydantic import BaseModel, EmailStr

class UserCreateRequest(BaseModel):
    username: str
    email: EmailStr
```

**Response:** `app/handler/entity/response/user.py`

```python
from datetime import datetime
from pydantic import BaseModel

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
```

### Step 6: 创建业务服务层

**File:** `app/service/user_service.py`

```python
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from app.repository.user_repository import UserRepository
from app.handler.entity.request.user import UserCreateRequest
from app.handler.entity.response.user import UserResponse

class UserService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.repo = UserRepository(db)
        self.redis = redis

    async def create_user(self, user_data: UserCreateRequest) -> UserResponse:
        cached = await self.redis.get(f"user:{user_data.username}")
        if cached:
            raise ValueError("Username already exists (cached)")

        existing = await self.repo.find_by_username(user_data.username)
        if existing:
            raise ValueError("Username already exists")

        user = await self.repo.create(user_data)
        await self.redis.set(f"user:{user.username}", user.email, ex=3600)

        return UserResponse.model_validate(user)

    async def get_user(self, user_id: int) -> UserResponse | None:
        user = await self.repo.find_by_id(user_id)
        if not user:
            return None
        return UserResponse.model_validate(user)
```

### Step 7: 重构 API 端点

**File:** `app/api/v1/endpoints/users.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.dependencies import get_db, get_redis
from app.service.user_service import UserService
from app.handler.entity.request.user import UserCreateRequest
from app.schemas.common import ApiResponse
from app.handler.entity.response.user import UserResponse

router = APIRouter()


@router.post("/", response_model=ApiResponse[UserResponse], status_code=201)
async def create_user(
    user_data: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    service = UserService(db, redis)
    try:
        user = await service.create_user(user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiResponse(message="success", status=0, data=user)


@router.get("/{user_id}", response_model=ApiResponse[UserResponse])
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    service = UserService(db, redis)
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return ApiResponse(message="success", status=0, data=user)
```

### Step 8: 更新 import 路径

需要更新以下文件的 import：
- `app/dependencies.py`
- `app/database.py`（如果需要引用 Base）
- `app/main.py`
- `alembic/env.py`（引用新的 Base 位置）

### Step 9: 删除旧文件

```bash
rm app/models/user.py
rm app/models/base.py
rm app/schemas/user.py
rm app/schemas/base.py
```

---

## 关键文件变更清单

| 操作 | 文件路径 |
|------|----------|
| 移动 | `app/models/user.py` → `app/repository/entity/user.py` |
| 移动 | `app/models/base.py` → `app/repository/entity/base.py` |
| 新建 | `app/repository/user_repository.py` |
| 新建 | `app/entity/user.py` |
| 移动 | `app/schemas/user.py` → `app/handler/entity/response/user.py` |
| 新建 | `app/handler/entity/request/user.py` |
| 新建 | `app/service/user_service.py` |
| 重构 | `app/api/v1/endpoints/users.py` |

---

## 验证步骤

1. **语法检查：**
   ```bash
   poetry run python -c "from app.main import app; print('OK')"
   ```

2. **启动服务：**
   ```bash
   poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **测试 API：**
   ```bash
   curl -X POST http://localhost:8000/api/v1/users/ \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","email":"test@example.com"}'
   ```

4. **运行测试：**
   ```bash
   poetry run pytest
   ```