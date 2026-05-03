# User Permission Management System Implementation Plan

## Context

User chose **full permission system** + **password field** authentication. Need to implement complete JWT authentication + RBAC role-permission + fine-grained permission control.

The system is divided into two independent modules:
- **Authentication.md** - Authentication module (user registration, login, JWT token)
- **Authorization.md** - Authorization module (RBAC role-permission, API protection)

---

## Technical Solution

### Database Model

```
users (existing, extended)
├── id, username, email (existing)
├── password_hash (new)
├── is_active (existing)
└── created_at, updated_at (existing)

roles
├── id, name, description
└── created_at

permissions
├── id, name, description
└── created_at

user_roles (many-to-many)
├── user_id, role_id
└── assigned_at

role_permissions (many-to-many)
├── role_id, permission_id
└── granted_at
```

### Permission Naming (Resource:Action)

```
users:read         # Read user list/details
users:write        # Create/update users
users:delete       # Delete users
roles:read         # Read roles
roles:write        # Create/update roles
roles:delete       # Delete roles
permissions:read  # Read permissions
```

### Default Roles

- `admin`: All permissions
- `editor`: users:read, users:write
- `viewer`: users:read

---

## Module Division

| Module | Document | Goal |
|--------|----------|------|
| Authentication | [Authentication.md](./Authentication.md) | User registration, login, JWT token issuance |
| Authorization | [Authorization.md](./Authorization.md) | RBAC role-permission, API protection |