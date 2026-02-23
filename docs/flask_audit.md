# Flask Application Audit Report

**Project**: SVG Translate Web
**Audit Date**: 2026-02-23
**Flask Skill Version**: 2.0.0 (January 2026)
**Auditor**: Claude Code

---

## Executive Summary

This audit assesses the SVG Translate Web application's compliance with Flask best practices as defined in the official Flask skill documentation. The application is a Flask-based web service for copying SVG translations between different language versions on Wikimedia Commons.

### Overall Grade: **B+ (Good with Minor Issues)**

The application follows many Flask best practices including the application factory pattern, Blueprint organization, and proper secret key management. However, several areas require attention to fully align with modern Flask standards and prevent potential production issues.

---

## Compliance Matrix

| Category            | Status           | Notes                                              |
| ------------------- | ---------------- | -------------------------------------------------- |
| Application Factory | ✅ Compliant     | Proper `create_app()` pattern implemented          |
| Blueprints          | ✅ Compliant     | Well-organized route structure                     |
| Configuration       | ⚠️ Partial       | Good structure, missing some Flask 3.1 features    |
| Extensions          | ⚠️ Partial       | CSRF enabled, but no centralized extensions module |
| Error Handling      | ⚠️ Partial       | Basic handlers present, missing common codes       |
| Threading/Context   | ❌ Non-Compliant | App context not properly passed to threads         |
| Testing             | ✅ Compliant     | Good test coverage with pytest                     |
| Security            | ⚠️ Partial       | Some Flask 3.1 security features missing           |

---

## Detailed Findings

### 🔴 Critical Issues (Must Fix)

#### Issue #1: Flask 3.1.2 stream_with_context Teardown Regression Risk

**Location**: `src/main_app/__init__.py:106-109`

**Problem**: The teardown handler does not follow the idempotent pattern required by Flask 3.1.2+ to prevent `KeyError` on multiple teardown calls.

**Current Code**:

```python
@app.teardown_appcontext
def _cleanup_connections(exception: Exception | None) -> None:
    close_cached_db()
    close_task_store()
```

**Risk**: If `stream_with_context` is used in the future or Flask internals change, this could cause `KeyError` exceptions during teardown.

**Recommendation**:

```python
@app.teardown_appcontext
def _cleanup_connections(exception: Exception | None) -> None:
    # Idempotent teardown - safe for Flask 3.1.2+ stream_with_context
    try:
        close_cached_db()
    except Exception:
        logger.debug("Failed to close cached DB during teardown", exc_info=True)
    try:
        close_task_store()
    except Exception:
        logger.debug("Failed to close task store during teardown", exc_info=True)
```

**Reference**: Flask Skill Issue #1, [GitHub Issue #5804](https://github.com/pallets/flask/issues/5804)

---

#### Issue #2: Application Context Lost in Background Threads

**Location**: `src/main_app/threads/task_threads.py:34-78`

**Problem**: Background threads are launched without properly pushing the Flask application context. The thread receives `settings.database_data` instead of the unwrapped app instance.

**Current Code**:

```python
def launch_task_thread(task_id, title, args, user_payload):
    cancel_event = threading.Event()
    _register_cancel_event(task_id, cancel_event)

    def _runner() -> None:
        try:
            run_task(
                settings.database_data,  # Passes config, not app context
                task_id,
                title,
                args,
                user_payload,
                cancel_event=cancel_event,
            )
        finally:
            _pop_cancel_event(task_id)

    t = threading.Thread(target=_runner, name=f"task-runner-{task_id[:8]}", daemon=True)
    t.start()
```

**Risk**: Code within `run_task()` cannot access `current_app`, Flask extensions, or any Flask-bound resources. This limits future extensibility and could cause runtime errors.

**Recommendation**:

```python
from flask import current_app

def launch_task_thread(task_id, title, args, user_payload):
    cancel_event = threading.Event()
    _register_cancel_event(task_id, cancel_event)

    # Unwrap the proxy object for use in thread
    app = current_app._get_current_object()

    def _runner() -> None:
        with app.app_context():  # Push app context in thread
            try:
                run_task(
                    app.config['settings'].database_data,
                    task_id,
                    title,
                    args,
                    user_payload,
                    cancel_event=cancel_event,
                )
            finally:
                _pop_cancel_event(task_id)

    t = threading.Thread(target=_runner, name=f"task-runner-{task_id[:8]}", daemon=True)
    t.start()
```

**Reference**: Flask Skill Issue #4, [Sentry.io Guide](https://sentry.io/answers/working-outside-of-application-context/)

---

#### Issue #3: Global State Won't Work in Multi-Process Environments

**Location**: `src/main_app/threads/task_threads.py:12-14`

**Problem**: The `CANCEL_EVENTS` dictionary is stored in process memory, which won't work correctly in multi-process deployments (e.g., Gunicorn with multiple workers).

**Current Code**:

```python
CANCEL_EVENTS: Dict[str, threading.Event] = {}
CANCEL_EVENTS_LOCK = threading.Lock()
```

**Risk**: When running with Gunicorn workers, each process has its own `CANCEL_EVENTS` dict. A cancellation request might hit a different worker than the one running the task, making cancellation unreliable.

**Recommendation**: Use a shared external store like Redis or the database:

```python
# Option 1: Database-backed cancellation
def get_cancel_event(task_id: str) -> threading.Event | None:
    # Check database for cancellation flag
    store = _get_task_store()
    if store.is_task_cancelled(task_id):
        event = threading.Event()
        event.set()
        return event
    return CANCEL_EVENTS.get(task_id)  # Fallback to local for in-progress

# Option 2: Redis-backed cancellation (recommended for production)
# Use Redis pub/sub or key-value store for cross-process cancellation
```

---

### 🟠 High Severity Issues (Should Fix)

#### Issue #4: Missing Flask 3.1 Security Configurations

**Location**: `src/main_app/__init__.py:52-125`

**Problem**: The application doesn't configure several Flask 3.1+ security features:

-   No `MAX_CONTENT_LENGTH` configured
-   No `MAX_FORM_MEMORY_SIZE` configured
-   No `MAX_FORM_PARTS` configured
-   No `SECRET_KEY_FALLBACKS` for key rotation

**Current Configuration**:

```python
app.config.update(
    SESSION_COOKIE_HTTPONLY=settings.cookie.httponly,
    SESSION_COOKIE_SECURE=settings.cookie.secure,
    SESSION_COOKIE_SAMESITE=settings.cookie.samesite,
)
```

**Recommendation**:

```python
app.config.update(
    SESSION_COOKIE_HTTPONLY=settings.cookie.httponly,
    SESSION_COOKIE_SECURE=settings.cookie.secure,
    SESSION_COOKIE_SAMESITE=settings.cookie.samesite,
    # Security configurations for Flask 3.1+
    MAX_CONTENT_LENGTH=100 * 1024 * 1024,  # 100MB for SVG uploads
    MAX_FORM_MEMORY_SIZE=16 * 1024 * 1024,  # 16MB form data in memory
    MAX_FORM_PARTS=1000,  # Limit form fields
    SECRET_KEY_FALLBACKS=settings.secret_key_fallbacks or [],
)
```

**Reference**: Flask Skill Issue #7, #8, Flask 3.1.0 Release Notes

---

#### Issue #5: No CSRF Token Lifetime Configuration

**Location**: `src/main_app/__init__.py:82-83`

**Problem**: CSRF protection is enabled but `WTF_CSRF_TIME_LIMIT` is not configured. This could lead to issues with cached pages serving expired tokens.

**Current Code**:

```python
csrf = CSRFProtect(app)  # noqa: F841
```

**Risk**: If any pages are cached longer than the default token lifetime (3600 seconds), users will receive "CSRF token expired" errors.

**Recommendation**:

```python
# Option 1: Extend token lifetime for cached pages
app.config['WTF_CSRF_TIME_LIMIT'] = 7200  # 2 hours

# Option 2: Disable expiration (less secure, for development only)
# app.config['WTF_CSRF_TIME_LIMIT'] = None

# Option 3: Add cache-busting headers for form pages
@app.after_request
def add_cache_headers(response):
    if request.method == 'GET' and request.endpoint and 'form' in request.endpoint:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response
```

**Reference**: Flask Skill Issue #6, [Flask-WTF Docs](https://flask-wtf.readthedocs.io/en/latest/csrf/)

---

#### Issue #6: Missing HTTP Error Handlers

**Location**: `src/main_app/__init__.py:111-123`

**Problem**: Only 404 and 500 errors are handled. Common errors like 400 (Bad Request), 403 (Forbidden), and 405 (Method Not Allowed) are not covered.

**Current Code**:

```python
@app.errorhandler(404)
def page_not_found(e: Exception) -> Tuple[str, int]:
    logger.error("Page not found: %s", e)
    flash("Page not found", "warning")
    return render_template("index.html", title="Page Not Found"), 404

@app.errorhandler(500)
def internal_server_error(e: Exception) -> Tuple[str, int]:
    logger.error("Internal Server Error: %s", e)
    flash("Internal Server Error", "danger")
    return render_template("index.html", title="Internal Server Error"), 500
```

**Recommendation**:

```python
@app.errorhandler(400)
def bad_request(e: Exception) -> Tuple[str, int]:
    logger.error("Bad request: %s", e)
    flash("Invalid request", "warning")
    return render_template("index.html", title="Bad Request"), 400

@app.errorhandler(403)
def forbidden(e: Exception) -> Tuple[str, int]:
    logger.error("Forbidden access: %s", e)
    flash("Access denied", "danger")
    return render_template("index.html", title="Access Denied"), 403

@app.errorhandler(405)
def method_not_allowed(e: Exception) -> Tuple[str, int]:
    logger.error("Method not allowed: %s", e)
    flash("Method not allowed", "warning")
    return render_template("index.html", title="Method Not Allowed"), 405

@app.errorhandler(CSRFError)
def handle_csrf_error(e: Exception) -> Tuple[str, int]:
    logger.error("CSRF error: %s", e)
    flash("Session expired. Please try again.", "warning")
    return render_template("index.html", title="Session Expired"), 400
```

---

#### Issue #7: Code Duplication in Task Store Singleton Pattern

**Location**:

-   `src/main_app/app_routes/tasks/routes.py:43-62`
-   `src/main_app/app_routes/cancel_restart/routes.py:36-48`

**Problem**: The `TASK_STORE` singleton pattern is duplicated across multiple modules, violating DRY principles.

**Current Code** (in both files):

```python
TASK_STORE: TaskStorePyMysql | None = None
TASKS_LOCK = threading.Lock()

def _task_store() -> TaskStorePyMysql:
    global TASK_STORE
    if TASK_STORE is None:
        TASK_STORE = TaskStorePyMysql(settings.database_data)
    return TASK_STORE
```

**Recommendation**: Create a centralized factory in `extensions.py`:

```python
# src/main_app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

# Task store factory with proper lifecycle management
_task_store_instance: TaskStorePyMysql | None = None
_task_store_lock = threading.Lock()

def get_task_store() -> TaskStorePyMysql:
    global _task_store_instance
    if _task_store_instance is None:
        with _task_store_lock:
            if _task_store_instance is None:
                _task_store_instance = TaskStorePyMysql(settings.database_data)
    return _task_store_instance

def close_task_store() -> None:
    global _task_store_instance
    with _task_store_lock:
        if _task_store_instance is not None:
            _task_store_instance.close()
            _task_store_instance = None
```

---

### 🟡 Medium Severity Issues (Consider Fixing)

#### Issue #8: No Extensions Module

**Location**: N/A (Missing file)

**Problem**: The application doesn't have a centralized `extensions.py` module for Flask extensions. Extensions are initialized directly in the factory.

**Current Pattern**:

```python
# In create_app()
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)  # Bound immediately
```

**Recommendation**: Create `src/main_app/extensions.py`:

```python
"""Flask extensions for dependency injection and avoiding circular imports."""

from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

# Import here to avoid circular imports
def get_task_store():
    from .db.task_store_pymysql import TaskStorePyMysql
    from .config import settings
    # ... singleton pattern
```

Then in `create_app()`:

```python
from .extensions import csrf, get_task_store

def create_app():
    app = Flask(__name__)
    csrf.init_app(app)
    # ...
```

**Reference**: Flask Skill "Extensions Module" pattern

---

#### Issue #9: Blueprints Don't Use Separate Template Folders

**Location**: All blueprint definitions

**Problem**: Blueprints don't define their own `template_folder`, forcing all templates into a single global namespace.

**Current Pattern**:

```python
# src/main_app/app_routes/main/routes.py
bp_main = Blueprint("main", __name__)
```

**Recommendation**:

```python
# src/main_app/app_routes/main/__init__.py
from flask import Blueprint

bp_main = Blueprint(
    "main",
    __name__,
    template_folder="templates",  # Blueprint-specific templates
)

from . import routes  # Import routes after bp creation
```

This allows templates to be organized as:

```
src/main_app/app_routes/main/templates/main/index.html
src/main_app/app_routes/auth/templates/auth/login.html
```

And referenced as:

```python
return render_template("main/index.html")
```

---

#### Issue #10: Custom Auth Instead of Flask-Login

**Location**: `src/main_app/users/current.py`, `src/main_app/app_routes/auth/routes.py`

**Problem**: The application implements a custom authentication system instead of using Flask-Login, missing out on:

-   Standardized session protection
-   `login_required` decorator (has custom implementation)
-   `current_user` proxy (has custom function)
-   Remember me functionality

**Current Implementation**:

```python
# Custom decorator
def oauth_required(func: F) -> F:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        if not current_user():
            session["post_login_redirect"] = request.url
            return redirect(url_for("auth.login"))
        return func(*args, **kwargs)
    return cast(F, wrapper)
```

**Note**: This is not strictly an issue since the custom implementation works for OAuth-only authentication. However, Flask-Login would provide better session security and standardization.

---

#### Issue #11: app.run() Used in Production Context

**Location**: `src/app.py:18-20`

**Problem**: While the application uses Gunicorn (per `requirements.txt`), the entry point still allows running with Flask's development server.

**Current Code**:

```python
if __name__ == "__main__":
    debug = "debug" in sys.argv or "DEBUG" in sys.argv
    app.run(debug=debug)
```

**Risk**: Accidental production deployment using `python app.py` instead of Gunicorn.

**Recommendation**: Add a warning when running in non-debug mode:

```python
if __name__ == "__main__":
    debug = "debug" in sys.argv or "DEBUG" in sys.argv
    if not debug:
        import warnings
        warnings.warn(
            "Running with Flask development server in production mode! "
            "Use Gunicorn for production deployments.",
            RuntimeWarning
        )
    app.run(debug=debug)
```

---

### 🟢 Low Severity / Recommendations

#### Issue #12: Template Path Configuration

**Location**: `src/main_app/__init__.py:66-70`

**Problem**: Template folder uses relative path `../templates` which could be fragile depending on working directory.

**Current Code**:

```python
app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static",
)
```

**Recommendation**: Use absolute paths based on the application root:

```python
from pathlib import Path

APP_ROOT = Path(__file__).parent.parent

app = Flask(
    __name__,
    template_folder=str(APP_ROOT / "templates"),
    static_folder=str(APP_ROOT / "static"),
)
```

---

#### Issue #13: Error Handler Returns Index Template

**Location**: `src/main_app/__init__.py:111-123`

**Problem**: Error handlers return the main `index.html` template instead of dedicated error pages.

**Current Code**:

```python
@app.errorhandler(404)
def page_not_found(e: Exception) -> Tuple[str, int]:
    flash("Page not found", "warning")
    return render_template("index.html", title="Page Not Found"), 404
```

**Recommendation**: Create dedicated error templates:

```python
@app.errorhandler(404)
def page_not_found(e: Exception) -> Tuple[str, int]:
    return render_template("errors/404.html"), 404
```

---

## Positive Findings

The following Flask best practices are correctly implemented:

### ✅ Application Factory Pattern

-   Proper `create_app()` function in `src/main_app/__init__.py`
-   Multiple app instances possible for testing
-   Configuration passed to factory

### ✅ Blueprint Organization

-   Logical separation of concerns across blueprints
-   Consistent naming convention (`bp_<name>`)
-   Proper URL prefix usage

### ✅ Configuration Management

-   Environment-based configuration via dataclasses
-   Required environment variables validated at startup
-   `SECRET_KEY` properly loaded from environment

### ✅ CSRF Protection

-   Flask-WTF CSRF protection enabled globally
-   Forms include CSRF tokens

### ✅ Database Cleanup

-   `teardown_appcontext` handler closes connections
-   Context manager pattern used for database operations

### ✅ Test Configuration

-   Comprehensive test suite with pytest
-   Fixtures in `conftest.py`
-   Environment variables set for testing

---

## Action Plan

### Phase 1: Critical Fixes (Immediate)

1. Fix teardown handler idempotency (Issue #1)
2. Pass app context to background threads (Issue #2)
3. Document multi-process deployment limitation (Issue #3)

### Phase 2: Security Hardening (1-2 weeks)

1. Add Flask 3.1 security configurations (Issue #4)
2. Configure CSRF token lifetime (Issue #5)
3. Add missing error handlers (Issue #6)

### Phase 3: Code Organization (2-4 weeks)

1. Create extensions module (Issue #8)
2. Centralize task store singleton (Issue #7)
3. Organize blueprint template folders (Issue #9)

### Phase 4: Nice to Have (Future)

1. Evaluate Flask-Login migration (Issue #10)
2. Create dedicated error templates (Issue #13)
3. Improve path configuration (Issue #12)

---

## Appendix: Flask Version Compatibility

| Feature                 | Current | Flask 3.1 Required | Status        |
| ----------------------- | ------- | ------------------ | ------------- |
| Application Factory     | ✅      | N/A                | Compatible    |
| Blueprints              | ✅      | N/A                | Compatible    |
| CSRF Protection         | ✅      | N/A                | Compatible    |
| stream_with_context fix | ❌      | 3.1.2+             | **Needs fix** |
| SECRET_KEY_FALLBACKS    | ❌      | 3.1.0+             | Optional      |
| MAX_CONTENT_LENGTH      | ⚠️      | 3.1.0+             | Recommended   |
| MAX_FORM_MEMORY_SIZE    | ❌      | 3.1.0+             | Recommended   |
| MAX_FORM_PARTS          | ❌      | 3.1.0+             | Recommended   |

---

## References

-   [Flask Documentation](https://flask.palletsprojects.com/)
-   [Flask 3.1.0 Release Notes](https://github.com/pallets/flask/releases/tag/3.1.0)
-   [Flask-WTF CSRF Documentation](https://flask-wtf.readthedocs.io/en/latest/csrf/)
-   Flask Skill Documentation (`.claude/flask/SKILL.md`)
-   [Gunicorn Documentation](https://docs.gunicorn.org/)
