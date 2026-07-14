# Flask-Security Migration Plan & Architectural Review

This document provides a highly comprehensive, step-by-step migration guide for integrating **Flask-Security-Too** into the existing codebase. The guide outlines how to replace the current custom session, cookie, and decorator-based authentication and authorization with the robust, community-standard Flask-Security-Too framework, while maintaining support for the application's MediaWiki OAuth 1.0a flow.

---

## 1. Executive Summary

The application currently relies on a bespoke authentication and authorization system integrated with MediaWiki OAuth 1.0a. While functional, custom auth implementations are prone to security vulnerabilities, lack extensibility, and increase the maintenance burden of the application.

By migrating to **Flask-Security-Too**, the application will gain:
1. **Industry-Standard Security:** Automatic protection against session fixation, secure cookie handling, and robust session management.
2. **Simplified RBAC/ABAC:** Native role-based (`@roles_required`) and permission-based (`@permissions_required`) decorators to replace bespoke decorators and manual conditional logic.
3. **Improved Testability:** Out-of-the-box utilities to mock authenticated users and roles during unit and integration testing.
4. **Future-Proofing:** Easy integration of advanced features such as two-factor authentication (2FA), API token authentication (via HTTP Token or JSON Web Tokens), and security logging, should they be required in the future.

This migration is designed **incrementally** to run the legacy auth and Flask-Security systems side-by-side during a transitional phase, eliminating system downtime and minimizing regression risks.

---

## 2. Current Architecture Analysis

The existing authentication mechanism leverages MediaWiki OAuth for secure user identification without storing password hashes.

### Legacy Components & Flows

1. **User Identity & Storage:**
   - `UserRecord` (`users` table): Stores the primary user identity (`username`) and system access capabilities (`can_run_jobs`, `can_run_bg_jobs`).
   - `UserTokenRecord` (`user_tokens` table): Holds the encrypted OAuth request/access tokens (`access_token`, `access_secret`).
   - `AdminUserRecord` (`admin_users` table): Acts as a role lookup table. If a user is active in this table, they are considered an administrator/coordinator.

2. **Session and Cookie Handlers:**
   - **Session:** Tracks `session["uid"]` and `session["username"]`.
   - **Cookie:** A signed fallback tracking cookie (`settings.cookie.name`) stores a signed user ID to restore sessions.
   - **Request Lifecycle Hook:** `before_app_request` calls `load_logged_in_user()`, which loads user data from the database and populates `g._current_user` with a `CurrentUser` dataclass composite.

3. **Bespoke Authorization Decorators:**
   - `@user_login_required`: Checks if `g._current_user` is present, flashing a warning and redirecting back if not.
   - `@oauth_required`: Checks for active OAuth credentials and redirects to `/login` if missing.
   - `@admin_required`: Validates that the loaded `g._current_user` has `is_active_admin == True` (queried via `is_active_coordinator(username)`).

---

## 3. Affected Components

The migration will touch several key layers across the application:

| Layer | Component Name | Action Required |
|---|---|---|
| **Dependencies** | `requirements.txt` | Add `Flask-Security-Too`, `email-validator`, and cryptography helpers. |
| **Configuration** | `src/main_app/config/` | Add Flask-Security configuration variables (e.g., `SECURITY_PASSWORD_REQUIRED = False`). |
| **Extensions** | `src/main_app/extensions/` | Instantiate the `Security` extension and register it with the app factory. |
| **Database Models** | `src/main_app/db/models/users.py` | Update `UserRecord` to inherit from `UserMixin` and add `fs_uniquifier`. Convert `AdminUserRecord` or create a new `Role` table matching Flask-Security expectations. |
| **Authentication Routes** | `src/main_app/public/auth/routes.py` | Integrate `login_user()` and `logout_user()` from Flask-Login/Flask-Security into the OAuth callback and logout routes. |
| **Middleware Hooks** | `src/main_app/public/auth/utils.py` | Refactor/retire `load_logged_in_user()` and transition global variable lookups to use Flask-Security's `current_user`. |
| **Decorators** | `src/main_app/admin/decorators.py` | Deprecate `@admin_required` in favor of `@roles_required('admin')` or `@permissions_required('admin')`. |
| **Blueprints & Routes** | `src/main_app/admin/routes/` and others | Replace bespoke route protectors with Flask-Security decorators. |
| **Templates** | `src/templates/` | Modify templates checking `g._current_user` to check Flask-Security's `current_user`. |

---

## 4. Authentication Flow & Dependency Graph

Below is an ASCII flow diagram representing how authentication currently traverses the system compared to how it will flow under **Flask-Security-Too**.

### Current (Legacy) Flow
```
[User Browser]
      │
      ├─► (Requests protected route)
      │         │
      │         ▼
  [Flask App Session] ──► (Verify session["uid"] or signed cookie)
      │                                │
      │                                ▼
      │                 [load_logged_in_user Hook]
      │                                │
      │                                ▼
      │                     [Query DB User & Token]
      │                                │
      │                                ▼
      │                     [Populate g._current_user]
      │                                │
      ▼                                ▼
[Route Decorators] ──────► [Verify g._current_user & Roles]
      │
      ├─► Access Allowed
      └─► Access Denied (Redirect to login or abort 403)
```

### Proposed Flask-Security-Too Integrated Flow
```
[User Browser]
      │
      ├─► (Requests protected route)
      │         │
      │         ▼
[Flask-Security-Too] ◄──► [Flask-Login Session Authenticator]
      │                                │
      │                                ▼
      │                     [Query DB User & Roles via]
      │                     [SQLAlchemyUserDatastore  ]
      │                                │
      │                                ▼
      │                    [Populate current_user proxy]
      │                                │
      ▼                                ▼
[FS Decorators] ─────────► [Verify current_user & roles/perms]
(e.g., @auth_required)                 │
                                       ├─► Access Allowed
                                       └─► Redirect to MW OAuth / Return 403 / 401
```

---

## 5. Phased Migration Strategy

To eliminate risk and guarantee continuous operation, a **4-Phase Migration Strategy** is recommended.

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: Database Schema Expansion & FS Initialization      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: Dual-Authentication Bridge (Coexistence Phase)     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 3: Route Decorator & Template Refactoring             │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 4: Deprecation, Cleanup & Hardening                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Phased Implementation Guide

### Phase 1: Database Schema Expansion & FS Initialization

#### Why this step is needed:
Flask-Security-Too requires specific database schemas (e.g., an active status field and a unique string identifier called `fs_uniquifier` on the user table, along with a role mapping table) to function correctly. This phase expands our current schemas without removing any existing tables or columns, ensuring full backwards compatibility.

#### Files that need modification:
- `requirements.txt`
- `src/main_app/db/models/users.py`
- `src/main_app/extensions/__init__.py`
- `src/main_app/config/flask_config.py`
- `src/main_app/__init__.py`

#### Expected code changes:

##### 1. Update Dependencies
Add the following to `requirements.txt`:
```text
Flask-Security-Too>=5.3.0
bcrypt>=4.0.0
```

##### 2. Update Database Models
We update `UserRecord` to implement the `UserMixin` interface and add `fs_uniquifier`. We also introduce a modern `RoleRecord` and a many-to-many helper table `roles_users`.

```python
# src/main_app/db/models/users.py
from flask_security import UserMixin, RoleMixin
import uuid

# Association table for User and Role models
roles_users = db.Table(
    "roles_users",
    db.Column("user_id", db.Integer(), db.ForeignKey("users.user_id", ondelete="CASCADE")),
    db.Column("role_id", db.Integer(), db.ForeignKey("roles.id", ondelete="CASCADE")),
)

class RoleRecord(db.Model, RoleMixin):
    """Flask-Security standard Role table."""
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # optional permissions list
    permissions: Mapped[str | None] = mapped_column(String(1024), nullable=True)

class UserRecord(db.Model, UserMixin):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    can_run_jobs: Mapped[int] = mapped_column(nullable=False, server_default=text("0"), default=0)
    can_run_bg_jobs: Mapped[int] = mapped_column(nullable=False, server_default=text("0"), default=0)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.current_timestamp())

    # Flask-Security requirements
    active: Mapped[bool] = mapped_column(nullable=False, server_default=text("1"), default=True)
    fs_uniquifier: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)

    # Relationships
    roles: Mapped[list[RoleRecord]] = relationship(
        "RoleRecord", secondary=roles_users, backref="users"
    )
    token: Mapped[UserTokenRecord | None] = relationship(back_populates="user", uselist=False)

    # Add property for Flask-Security ID lookup
    @property
    def id(self) -> int:
        return self.user_id
```

##### 3. Initialize Flask-Security-Too in Extensions
```python
# src/main_app/extensions/__init__.py
from flask_security import Security, SQLAlchemyUserDatastore

# Instantiate Security extension
security = Security()
```

##### 4. Set Flask-Security Configurations
Add standard settings to `Config` class to allow session-based passwordless OAuth login.
```python
# src/main_app/config/flask_config.py
class Config:
    # ... previous config values ...

    # Flask-Security Configuration
    SECURITY_PASSWORD_REQUIRED = False
    SECURITY_REGISTERABLE = False
    SECURITY_RECOVERABLE = False
    SECURITY_CONFIRMABLE = False
    SECURITY_CHANGEABLE = False
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_SEND_PASSWORD_CHANGE_EMAIL = False
    SECURITY_SEND_PASSWORD_RESET_NOTICE_EMAIL = False

    # Session configurations
    SECURITY_URL_PREFIX = "/auth"
    SECURITY_FLASH_MESSAGES = True

    # Disable default built-in views to retain our custom OAuth flows
    SECURITY_LOGIN_VIEW = "/login"
    SECURITY_POST_LOGOUT_VIEW = "/"
    SECURITY_UNAUTHORIZED_VIEW = None
```

##### 5. Initialize inside App Factory
```python
# src/main_app/__init__.py
from .extensions import security
from .db.models.users import UserRecord, RoleRecord

def create_app(config_class: Type) -> Flask:
    # ... standard setup ...
    _db.init_app(app)

    # Initialize Flask-Security with custom SQLAlchemyUserDatastore
    user_datastore = SQLAlchemyUserDatastore(_db, UserRecord, RoleRecord)
    security.init_app(app, datastore=user_datastore)

    # ... remain of app initialization ...
```

#### Potential Issues:
- **Migration scripts execution:** Existing SQLite schemas in tests must generate `fs_uniquifier` and `active` automatically without breaking current constraints.
- **Null values in SQLite/MySQL production databases:** When adding `fs_uniquifier` as a non-nullable unique column, existing records must receive a populated unique string. A database migration step utilizing a data migration script (e.g., generating UUIDs for every user) is mandatory.

#### Verification & Testing:
- Verify that SQLAlchemy builds the schemas successfully using `init_db`.
- Run tests via `python3 -m pytest tests/unit/` to confirm that schema modification did not break existing query execution or user instantiation.

---

### Phase 2: Dual-Authentication Bridge (Coexistence Phase)

#### Why this step is needed:
To prevent breaking existing sessions and to ensure both the legacy `g._current_user` system and Flask-Security's session manager function correctly during transition, we bridge them inside the OAuth authentication endpoints.

#### Files that need modification:
- `src/main_app/public/auth/routes.py`
- `src/main_app/public/auth/utils.py`

#### Expected code changes:

##### 1. Upgrade OAuth Callback Route
During a successful OAuth login, we programmatically call Flask-Security's `login_user()` helper. This guarantees that Flask-Login sets session variables (`user_id`, `remember`) under the hood, while preserving our traditional custom session and cookies.

```python
# src/main_app/public/auth/routes.py
from flask_security import login_user, logout_user

# Inside callback():
            # ... previous oauth validation checks ...
            user_id = user_record.user_id

            # Legacy session configuration
            session["uid"] = user_id
            session["username"] = user_record.username

            # Set response and cookies
            response = make_response(redirect(session.pop("post_login_redirect", url_for("main.index"))))
            _set_response_cookies(user_id, response)

            # --- FLASK-SECURITY BRIDGE ---
            # Automatically logs the user into Flask-Security/Flask-Login session context
            login_user(user_record, remember=True)

            # Cache in g for legacy backward compatibility
            g._current_user = user_record
            return response

# Inside logout():
            user_id = session.pop("uid", None)
            session.pop(request_token_key, None)
            session.pop(oauth_state_nonce, None)
            session.pop("username", None)

            # --- FLASK-SECURITY BRIDGE ---
            logout_user() # Clean up Flask-Security/Flask-Login session state

            # ... legacy token cleanup and response handling ...
```

##### 2. Keep `load_logged_in_user` Backwards Compatible
We can modify `load_logged_in_user()` to automatically populate Flask-Security context if only the legacy session exists, or vice versa, ensuring dual state alignment.

```python
# src/main_app/public/auth/utils.py
from flask_security import login_user, current_user

def load_logged_in_user() -> None:
    if hasattr(g, "_current_user") and g._current_user is not None:
        return

    # Check Flask-Login (current_user is authenticated)
    if current_user.is_authenticated:
        g._current_user = current_user
        session["uid"] = current_user.user_id
        session["username"] = current_user.username
        return

    # Fallback to legacy cookie or session
    user_id = session.get("uid")
    # ... rest of legacy resolve logic ...

    if user_id is not None:
        user = AuthUserService.get_authenticated_user(user_id)
        g._current_user = user
        if user:
            # Sync with Flask-Login
            login_user(user, remember=True)
```

#### Potential Issues:
- Cookie domain/path configuration issues might trigger loop redirects or session loss if Flask-Security overrides existing cookie properties. Ensure `SECURITY_COOKIE_NAME` is configured uniquely or matches settings.

#### Verification & Testing:
- Perform full local user sign-in/sign-out simulations.
- Assert that visiting routes protected by both current and legacy auth models works seamlessly.

---

### Phase 3: Route Decorator & Template Refactoring

#### Why this step is needed:
Once the authentication contexts are unified, we can confidently replace bespoke decorators (`@admin_required`, `@oauth_required`, `@user_login_required`) with the built-in Flask-Security decorators, and change template references from `g._current_user` to the template context variable `current_user`.

#### Files that need modification:
- `src/main_app/admin/routes/*.py`
- `src/main_app/public/main_routes/*.py`
- `src/templates/**/*.html`

#### Expected code changes:

##### 1. Refactor Blueprint/Route Protections (Decorators)
Refer to the **Decorator Mapping Table** and **Code Refactoring** section below for granular details. Here is an example refactor for `UsersRoutes`:

```python
# src/main_app/admin/routes/users.py (AFTER MIGRATION)
from flask_security import auth_required, roles_required

class UsersRoutes:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.bp.route("/", methods=["GET"])
        @roles_required("admin")
        def dashboard():
            return _dashboard()

        @self.bp.post("/<int:user_id>/can_run_jobs")
        @roles_required("admin")
        def update_can_run_jobs(user_id: int) -> ResponseReturnValue:
            # ... method logic ...
```

##### 2. HTML Template Refactoring
Modify checks in templates.
**Before:**
```html
{% if g._current_user %}
  <p>Welcome, {{ g._current_user.username }}!</p>
  {% if g._current_user.is_active_admin %}
    <a href="/admin">Admin Panel</a>
  {% endif %}
{% endif %}
```

**After:**
```html
{% if current_user.is_authenticated %}
  <p>Welcome, {{ current_user.username }}!</p>
  {% if current_user.has_role('admin') %}
    <a href="/admin">Admin Panel</a>
  {% endif %}
{% endif %}
```

#### Verification & Testing:
- Run automated tests to check that route accesses by non-authenticated/non-admin users return the correct status codes (`302 Redirect` for auth required, `403 Forbidden` for role missing).

---

### Phase 4: Deprecation, Cleanup & Hardening

#### Why this step is needed:
With all routes migrated, we remove the legacy session/cookie recovery mechanisms, deprecate unused files, and lock down security options to minimize attack surface area.

#### Files that need modification:
- `src/main_app/admin/decorators.py` (Delete/deprecate)
- `src/main_app/public/auth/utils.py` (Delete legacy logic)
- `src/main_app/shared/auth/current_user.py` (Remove `CurrentUser` dataclass)

#### Cleaned-up code details:
- Completely remove `load_logged_in_user` before-request handler.
- Update `AuthUserService` to return the SQLAlchemy model `UserRecord` instead of `CurrentUser` composite.

---

## 7. Decorator Mapping Table

| Legacy/Custom Decorator | Flask-Security Equivalent | Action & Implementation Details |
|---|---|---|
| `@oauth_required` | `@auth_required("session")` | Requires active authenticated session. Redirects to `/login` if unauthenticated. |
| `@user_login_required`| `@auth_required()` | Standard authentication check. Handled by Flask-Security internally. |
| `@admin_required` | `@roles_required("admin")` | Restricts access to users belonging to the `admin` role. Returns `403 Forbidden` on failure. |
| *Bespoke Job permissions checks* (e.g., `user.can_run_jobs`) | `@permissions_required("run_jobs")` | Map `can_run_jobs` column to a fine-grained role or standard permission inside the Flask-Security schema. |

---

## 8. Code Refactoring (Before / After Examples)

### Route Protection Example

#### Existing Code (Custom decorators)
```python
from ...admin.decorators import admin_required

@self.bp.route("/coordinators", methods=["GET"])
@admin_required
def show_coordinators():
    return render_template("admins/coordinators.html")
```

#### Recommended Flask-Security-Too Replacement
```python
from flask_security import roles_required

@self.bp.route("/coordinators", methods=["GET"])
@roles_required("admin")
def show_coordinators():
    return render_template("admins/coordinators.html")
```

#### Why the replacement is correct:
The custom decorator `@admin_required` executes manually written query logic checking `AdminUserRecord` via `is_active_coordinator(username)`. This is highly coupled and must be maintained. `@roles_required("admin")` is fully optimized, uses Flask-Security cached user associations, automatically handles response formats (HTML redirects vs. JSON error payloads), and implements standards compliance.

---

### Current User Usage Example

#### Existing Code
```python
from flask import g

@self.bp.route("/profile")
def profile():
    user = getattr(g, "_current_user", None)
    if not user:
        abort(401)
    return f"User ID: {user.user_id}, Username: {user.username}"
```

#### Recommended Flask-Security-Too Replacement
```python
from flask_security import current_user, auth_required

@self.bp.route("/profile")
@auth_required()
def profile():
    return f"User ID: {current_user.id}, Username: {current_user.username}"
```

#### Why the replacement is correct:
Instead of relying on a manually populated global context variable `g._current_user` that is loosely bound to the request thread, we use Flask-Security's thread-safe proxy `current_user`. This reduces logic errors during complex asynchronous execution or task background-processing.

---

## 9. Risk Analysis, Testing & Rollback Plan

### Risk Assessment & Mitigation

| Phase / Component | Identified Risk | Mitigation Strategy |
|---|---|---|
| **Phase 1** | Schema expansion fails on MySQL database (duplicate keys / constraint errors with `fs_uniquifier`). | Deploy a pre-migration schema check. Pre-populate the table with unique hash strings via a secure SQL script *before* applying the strict unique constraint. |
| **Phase 2** | Redirection loop between custom login route `/login` and Flask-Security's unauthorized redirects. | Configure `SECURITY_LOGIN_VIEW = '/login'` and disable built-in login views (`SECURITY_VIEWS = False` or explicit blueprint configurations) so that Flask-Security defers fully to the existing handler. |
| **Phase 3** | Access loss to administrative pages because Role attributes aren't linked to `AdminUserRecord`. | In the SQLAlchemy User datastore, sync coordinators to the `admin` role automatically inside the OAuth callback process. |

### Testing Strategy

1. **Unit Testing:**
   - Write tests simulating authenticated requests by using Flask-Security-Too's test context login manager:
     ```python
     from flask_security import login_user

     def test_admin_route_as_admin(client, app, user_datastore):
         with app.test_request_context():
             admin_user = user_datastore.find_user(username="AdminUser")
             login_user(admin_user)
             # execute client tests...
     ```
2. **Integration Testing:**
   - Execute a series of unauthorized requests checking that `401` or `403` responses are consistently generated.
3. **Regressions Checks:**
   - Run existing unit tests: `python3 -m pytest tests/unit/` to verify that data processing pipelines, template parsers, and cron workers are fully insulated from Auth engine changes.

### Rollback Strategy

Should any phase encounter critical errors in production, follow these steps to restore service:

1. **Phase 1/2 Failure:**
   - Revert code commits from the deployment branch.
   - Run Alembic downgrade command if schema modifications have been committed:
     ```bash
     flask db downgrade
     ```
2. **Session / Cache issues:**
   - Flush application session caches or force session invalidation (cookie renaming) to clear state mismatches between Legacy session keys (`uid`) and Flask-Security cookies.

---

## 10. Best Practices & Post-Migration Cleanup

- **Session Hardening:** Configure `SESSION_COOKIE_SECURE=True` and `SESSION_COOKIE_HTTPONLY=True` in production.
- **CSRF Synchronization:** Align Flask-WTF CSRF configurations with Flask-Security's inner CSRF validators.
- **Service Layer Separation:** Keep business logic decoupled from `current_user` objects. Pass simple values (`username`, `user_id`) to background workers rather than full ORM models.
- **Role/Permission Caching:** For large-scale data sets, use Redis to cache Flask-Security role lookup queries to keep latency low.
- **Remove Orphaned Code:** Once fully migrated, delete unused modules (`src/main_app/admin/decorators.py` and old custom cookies utility files).

---
*Migration Plan approved for implementation.*
