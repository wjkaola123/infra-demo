# 用户权限管理系统实现计划

## Context

用户选择了**完整权限系统** + **password字段**方式认证。需要实现完整的 JWT 认证 + RBAC 角色权限 + 细粒度权限控制。

整个系统分为两个独立模块：
- **Authentication.md** - 认证模块（用户注册、登录、JWT 令牌）
- **Authorization.md** - 鉴权模块（RBAC 角色权限、API 保护）

---

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

## 模块划分

| 模块 | 文档 | 目标 |
|------|------|------|
| 认证 | [Authentication.md](./Authentication.md) | 用户注册、登录、JWT 令牌发放 |
| 鉴权 | [Authorization.md](./Authorization.md) | RBAC 角色权限、API 保护 |