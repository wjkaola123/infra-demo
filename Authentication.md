# 认证模块 (Authentication)

**目标：** 实现用户注册、登录、JWT 令牌发放功能。

## Context

用户选择了**完整权限系统** + **password字段**方式认证。认证模块是第一步，主要实现用户身份验证和 JWT 令牌发放。

## 技术方案

### 数据库模型

```
users (已存在, 扩展)
├── id, username, email (已有)
├── password_hash (新增)
├── is_active (已有)
└── created_at, updated_at (已有)
```

## 实施步骤

### Step 1.1: 添加依赖

**pyproject.toml 新增:
```toml
python-jose = "^3.3.0"
passlib = {extras = ["bcrypt"]}
python-multipart = "^0.0.9"
```

### Step 1.2: 扩展 User 模型

**app/repository/entity/user.py:**
- 新增 `password_hash` 字段

### Step 1.3: 创建认证服务

**app/tools/auth/hashing.py:**
- 密码哈希/验证 (bcrypt)

**app/tools/auth/jwt.py:**
- `JWTHandler` 类 - 创建/验证 token
- `create_access_token()`
- `create_refresh_token()`
- `decode_token()`
- `verify_token()`

**app/service/auth_service.py:**
- `AuthService` 类 - 封装注册/登录/刷新token业务逻辑

### Step 1.4: 创建认证 API

**app/api/v1/endpoints/auth.py:**
```
POST /api/v1/auth/register   - 注册用户
POST /api/v1/auth/login      - 登录获取JWT
POST /api/v1/auth/refresh    - 刷新Token
```

### Step 1.5: 创建 Alembic 迁移

```
002_add_password_hash_to_users.py
```

## 关键文件

| 文件 | 用途 |
|------|------|
| `app/repository/entity/user.py` | User 模型 (新增 password_hash) |
| `app/tools/auth/hashing.py` | 密码加密/验证 |
| `app/tools/auth/jwt.py` | JWT 工具类 |
| `app/service/auth_service.py` | 认证业务逻辑 |
| `app/api/v1/endpoints/auth.py` | 认证 API (register/login/refresh) |

## 验证方案

```bash
# 1. 启动服务
docker-compose up -d --build

# 2. 运行迁移
poetry run alembic upgrade head

# 3. 测试注册
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","email":"admin@test.com","password":"admin123"}'

# 4. 测试登录获取token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin&password=admin123"

# 5. 测试刷新token
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Authorization: Bearer <refresh_token>"
```