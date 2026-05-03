# Authorization Module

**Goal:** Implement RBAC role-permission system, protect API endpoints.

## Context

The authorization module depends on the authentication module. After a user obtains a JWT token, the role and permission system controls the user's access to the API.

## Technical Solution

### Database Model

```
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

## Implementation Steps

### Step 2.1: Create Permission-related Models

**app/repository/entity/role.py:**
```python
- Role model
- Permission model
- user_roles association table
- role_permissions association table
```

### Step 2.2: Create Authorization Dependency Injection

**app/dependencies.py:**
- `get_current_user()` - Get current user from JWT
- `require_permissions(*perms)` - Permission check decorator

### Step 2.3: Protect Existing APIs

Add permission dependencies to users API:
```
GET /api/v1/users/           - require_permissions("users:read")
POST /api/v1/users/          - require_permissions("users:write")
GET /api/v1/users/{id}       - require_permissions("users:read")
PUT /api/v1/users/{id}       - require_permissions("users:write")
DELETE /api/v1/users/{id}    - require_permissions("users:delete")
```

### Step 2.4: Create Alembic Migration

```
003_create_roles_permissions_tables.py
```

### Step 2.5: Write Test Cases

```
test_requires_auth.py
test_permission_check.py
```

## Key Files

| File | Purpose |
|------|---------|
| `app/repository/entity/role.py` | Role/Permission ORM models |
| `app/dependencies.py` | get_current_user, require_permissions |

## Verification Plan

```bash
# 1. Access without token should return 401
curl http://localhost:8000/api/v1/users/  # 401 Unauthorized

# 2. Access protected endpoint with token
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/users/

# 3. User without permission should return 403
curl -H "Authorization: Bearer <viewer_token>" \
  -X DELETE http://localhost:8000/api/v1/users/1  # 403 Forbidden
```