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

#### 1. 中间件 `app/middleware/audit_middleware.py`

拦截 `POST`/`DELETE` 请求，自动捕获：
- 从 `get_current_user()` 获取操作人
- 从请求体解析 `new_value`（CREATE）
- 从响应 body 解析 `resource_id`（CREATE）
- DELETE 时 old_value 通过请求路径 `/{resource_type}/{resource_id}` 查库获取
- 异步写入 ActivityLog

中间件注册到 `app/main.py`。

#### 2. Service 层 UPDATE 补钩

在 `UserService`/`RoleService`/`PermissionService` 的 `update_*` 方法末尾，调用 `ActivityLogService.log_update()`。

old_value 和 new_value 由 Service 层传入（UPDATE 前查一次库，UPDATE 后自行构造）。

#### 3. ActivityLogService

提供三个方法：
```python
async def log_create(db, actor_user_id, actor_username, resource_type, resource_id, new_value, ip_address)
async def log_update(db, actor_user_id, actor_username, resource_type, resource_id, old_value, new_value)
async def log_delete(db, actor_user_id, actor_username, resource_type, resource_id, old_value, ip_address)
```

### 目录结构

```
app/
├── middleware/
│   └── audit_middleware.py
├── repository/entity/
│   └── activity_log.py
├── repository/
│   └── activity_log_repository.py
├── service/
│   └── activity_log_service.py
└── api/v1/endpoints/
    └── activity_logs.py
```

## 验证

- 启动服务后，创建/更新/删除 User/Role/Permission，数据库 `activity_logs` 表有对应记录
- GET `/api/v1/activity-logs/` 能返回分页数据
- 各过滤条件（actor_user_id, resource_type, action, date range）单独和组合生效
