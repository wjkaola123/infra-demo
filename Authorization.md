# 鉴权模块 (Authorization)

**目标：** 实现 RBAC 角色权限系统，保护 API 端点。

## Context

鉴权模块依赖认证模块。在用户获得 JWT token 后，通过角色和权限系统控制用户对 API 的访问。

## 技术方案

### 数据库模型

```
roles
├── id, name, description
└── created_at

permissions
├── id, name, description
└── created_at

user_roles (多对多)
├── user_id, role_id
└── assigned_at

role_permissions (多对多)
├── role_id, permission_id
└── granted_at
```

### 权限命名 (Resource:Action)

```
users:read         # 读取用户列表/详情
users:write        # 创建/更新用户
users:delete       # 删除用户
roles:read         # 读取角色
roles:write        # 创建/更新角色
roles:delete       # 删除角色
permissions:read  # 读取权限
```

### 默认角色

- `admin`: 全部权限
- `editor`: users:read, users:write
- `viewer`: users:read

## 实施步骤

### Step 2.1: 创建权限相关模型

**app/repository/entity/role.py:**
```python
- Role 模型
- Permission 模型
- user_roles 关联表
- role_permissions 关联表
```

### Step 2.2: 创建鉴权依赖注入

**app/dependencies.py:**
- `get_current_user()` - 从 JWT 获取当前用户
- `require_permissions(*perms)` - 权限检查装饰器

### Step 2.3: 保护现有 API

在 users API 添加权限依赖:
```
GET /api/v1/users/           - require_permissions("users:read")
POST /api/v1/users/          - require_permissions("users:write")
GET /api/v1/users/{id}       - require_permissions("users:read")
PUT /api/v1/users/{id}       - require_permissions("users:write")
DELETE /api/v1/users/{id}    - require_permissions("users:delete")
```

### Step 2.4: 创建 Alembic 迁移

```
003_create_roles_permissions_tables.py
```

### Step 2.5: 编写测试用例

```
test_requires_auth.py
test_permission_check.py
```

## 关键文件

| 文件 | 用途 |
|------|------|
| `app/repository/entity/role.py` | Role/Permission ORM 模型 |
| `app/dependencies.py` | get_current_user, require_permissions |

## 验证方案

```bash
# 1. 无token访问应返回401
curl http://localhost:8000/api/v1/users/  # 401 Unauthorized

# 2. 使用token访问受保护接口
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/users/

# 3. 无权限用户访问应返回403
curl -H "Authorization: Bearer <viewer_token>" \
  -X DELETE http://localhost:8000/api/v1/users/1  # 403 Forbidden
```