# Activity Log Module Design

## Context

记录用户对 User/Role/Permission 的所有变更操作（CREATE/UPDATE/DELETE），并在管理界面展示日志，供管理员追溯操作历史。

## Design

### 数据模型

**Entity:** `ActivityLog` (ORM model in `app/repository/entity/activity_log.py`)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | 主键 |
| `actor_user_id` | Integer | 操作人 ID |
| `actor_username` | String(50) | 操作人用户名（冗余存储） |
| `action` | String(20) | `CREATE` / `UPDATE` / `DELETE` |
| `resource_type` | String(20) | `user` / `role` / `permission` |
| `resource_id` | Integer | 资源 ID |
| `old_value` | JSON | 变更前值（UPDATE/DELETE） |
| `new_value` | JSON | 变更后值（CREATE/UPDATE） |
| `ip_address` | String(45) | 请求 IP（支持 IPv6） |
| `created_at` | DateTime | 操作时间 |

表名：`activity_logs`

继承：`Base`, `TimestampMixin`

### API 端点

**GET /api/v1/activity-logs/** — 查询日志列表（分页 + 多条件过滤）

Query 参数：
- `page: int = 1`
- `page_size: int = 20`
- `actor_user_id: int | None`
- `resource_type: str | None` — `user` / `role` / `permission`
- `action: str | None` — `CREATE` / `UPDATE` / `DELETE`
- `start_date: datetime | None`
- `end_date: datetime | None`

返回：`ApiResponse[Page[ActivityLogResponse]]`，按 `created_at` 倒序。

Response DTO (`ActivityLogResponse`):
```python
actor_user_id: int
actor_username: str
action: str
resource_type: str
resource_id: int
old_value: dict | None
new_value: dict | None
ip_address: str | None
created_at: datetime
```

权限：登录用户均可查看。

### 集成点

#### 1. 用户上下文 ContextVar

为解决 SQLAlchemy 事件无法访问请求上下文的问题，使用 `contextvars` 在请求生命周期内传递用户信息。

新建 `app/context.py`：
```python
from contextvars import ContextVar
from dataclasses import dataclass

@dataclass
class AuditContext:
    user_id: int
    username: str
    ip_address: str | None = None

audit_context: ContextVar[AuditContext | None] = ContextVar("audit_context", default=None)
```

在 `dependencies.py` 的 `get_current_user()` 中设置 context：
```python
# 设置审计上下文
audit_context.set(AuditContext(user_id=current_user.id, username=current_user.username, ip_address=request.client.host))
```

#### 2. SQLAlchemy 事件监听

在 `app/repository/entity/` 各实体模型上注册事件监听。

**CREATE（after_insert）** — 记录新增
```python
@event.listens_for(User, "after_insert")
def receive_after_insert(mapper, connection, target):
    ctx = audit_context.get()
    if ctx:
        write_activity_log(mapper, connection, "CREATE", target, None, target.to_dict())
```

**UPDATE（before_update` + `after_update）** — 记录变更前后
```python
@event.listens_for(User, "before_update")
def receive_before_update(mapper, connection, target):
    # 在更新前捕获旧值，存入 target 的历史字段
    target._old_values = {c.name: getattr(target, c.name) for c in target.__table__.columns}

@event.listens_for(User, "after_update")
def receive_after_update(mapper, connection, target):
    ctx = audit_context.get()
    if ctx and hasattr(target, "_old_values"):
        write_activity_log(mapper, connection, "UPDATE", target, target._old_values, target.to_dict())
        del target._old_values
```

**DELETE（before_delete）** — 记录删除前
```python
@event.listens_for(User, "before_delete")
def receive_before_delete(mapper, connection, target):
    ctx = audit_context.get()
    if ctx:
        write_activity_log(mapper, connection, "DELETE", target, target.to_dict(), None)
```

`write_activity_log` 内部创建 `ActivityLog` 记录并插入。

#### 3. ActivityLogRepository

提供 `create(activity_log: ActivityLog)` 方法，供事件监听器调用。

### 目录结构

```
app/
├── context.py                      # 新增：审计上下文 ContextVar
├── repository/entity/
│   ├── activity_log.py             # 新增：ActivityLog ORM 模型
│   ├── user.py                      # 修改：注册事件监听
│   ├── role.py                      # 修改：注册事件监听
│   └── permission.py               # 修改：注册事件监听
├── repository/
│   └── activity_log_repository.py   # 新增：日志仓储
└── api/v1/endpoints/
    └── activity_logs.py            # 新增：日志查询 API
```

依赖注入：`ActivityLogRepository` 通过 `get_db()` 获取 session 即可，无需特殊 DI。

## 验证

- 启动服务后，创建/更新/删除 User/Role/Permission，数据库 `activity_logs` 表有对应记录
- old_value / new_value 正确捕获变更前后数据
- GET `/api/v1/activity-logs/` 能返回分页数据
- 各过滤条件（actor_user_id, resource_type, action, date range）单独和组合生效
