# 用户权限管理系统实现计划

## Context

用户选择了**完整权限系统** + **password字段**方式认证。需要实现完整的 JWT 认证 + RBAC 角色权限 + 细粒度权限控制。

## 技术方案

### 数据库模型

```
users (已存在, 扩展)
├── id, username, email (已有)
├── password_hash (新增)
├── is_active (已有)
└── created_at, updated_at (已有)

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

---

## 实施步骤

### Step 1: 添加依赖

**pyproject.toml 新增:**
```toml
python-jose = "^3.3.0"
passlib = {extras = ["bcrypt"]}
python-multipart = "^0.0.9"
```

### Step 2: 扩展 User 模型

**app/repository/entity/user.py:**
- 新增 `password_hash` 字段

### Step 3: 创建权限相关模型

**app/repository/entity/role.py:**
```python
- Role 模型
- Permission 模型
- user_roles 关联表
- role_permissions 关联表
```

### Step 4: 创建认证服务

**app/auth/jwt.py:**
- `JWTHandler` 类 - 创建/验证 token
- `create_access_token()`
- `decode_token()`

**app/auth/hashing.py:**
- `HashHandler` 类
- `verify_password()` - bcrypt 验证
- `get_password_hash()` - 生成哈希

### Step 5: 创建依赖注入

**app/dependencies.py:**
- `get_current_user()` - 从 JWT 获取当前用户
- `require_permissions(*perms)` - 权限检查装饰器

### Step 6: 创建认证 API

**app/api/v1/endpoints/auth.py:**
```
POST /api/v1/auth/register   - 注册用户
POST /api/v1/auth/login      - 登录获取JWT
POST /api/v1/auth/refresh    - 刷新Token
```

### Step 7: 保护现有 API

在 users API 添加权限依赖:
```
GET /api/v1/users/           - require_permissions("users:read")
POST /api/v1/users/          - require_permissions("users:write")
GET /api/v1/users/{id}       - require_permissions("users:read")
PUT /api/v1/users/{id}       - require_permissions("users:write")
DELETE /api/v1/users/{id}    - require_permissions("users:delete")
```

### Step 8: 创建 Alembic 迁移

```
001_add_password_hash_to_users.py
002_create_roles_permissions_tables.py
```

### Step 9: 编写测试用例

```
test_auth_register.py
test_auth_login.py
test_requires_auth.py
test_permission_check.py
```

---

## 关键文件

| 文件 | 用途 |
|------|------|
| `app/repository/entity/role.py` | Role/Permission ORM 模型 |
| `app/auth/jwt.py` | JWT 工具类 |
| `app/auth/hashing.py` | 密码加密 |
| `app/auth/dependencies.py` | get_current_user, require_permissions |
| `app/api/v1/endpoints/auth.py` | 认证 API |

---

## 验证方案

```bash
# 1. 启动服务
docker-compose up -d --build

# 2. 运行迁移
alembic upgrade head

# 3. 测试注册
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","email":"admin@test.com","password":"admin123"}'

# 4. 测试登录获取token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin&password=admin123"

# 5. 使用token访问受保护接口
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/users/

# 6. 无token访问应返回401
curl http://localhost:8000/api/v1/users/  # 401 Unauthorized
```
