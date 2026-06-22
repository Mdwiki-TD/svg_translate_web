# Violation Patterns Reference

This file lists every detectable Separation of Concerns violation pattern
for Flask-SQLAlchemy projects, organized by the **offending layer**.

---

## 1. Route / View Violations (`public/`)

### V-R1 · Business logic in route functions

**Pattern**: Conditional branching, calculations, or data transformation that
belongs in a service.
**Detection**: Route function body > 25 lines; `if`/`for` blocks not related to
request parsing or response building.
**Severity**: 🟠 High

### V-R2 · Direct ORM queries in routes

**Pattern**: `db.session.query(...)`, `Model.query.filter(...)`, or
`db.session.add/commit` called directly inside a route.
**Detection**: Import of `db` from `extensions` in a route file AND `.query.`,
`.session.` usage in the route body.
**Severity**: 🔴 Critical

### V-R3 · Direct import of models in routes

**Pattern**: `from main_app.db.models.user import User` inside `public/`.
**Detection**: Any `from ...db.models` import in a route file.
**Severity**: 🟠 High (routes should call services, not models directly)

### V-R4 · Raw SQL in routes

**Pattern**: `db.session.execute("SELECT ...")` or `text(...)` in a route.
**Severity**: 🔴 Critical

### V-R5 · Response formatting in routes that should be Jinja filters

**Pattern**: String manipulation of dates, currencies, or HTML inside a route
function that is already handled (or should be) by a Jinja filter in `core/jinja_filters.py`.
**Severity**: 🟢 Low

---

## 2. Model Violations (`db/models/`)

### V-M1 · Cross-model queries inside model methods

**Pattern**: A method on `ModelA` imports or queries `ModelB`.
**Detection**: Import of another model inside a model file AND usage in an
instance/class method.
**Severity**: 🟠 High

### V-M2 · Business logic in model methods

**Pattern**: Complex orchestration logic (e.g., sending emails, updating
multiple records, applying discount rules) inside a model method instead of a service.
**Detection**: Model methods with >10 lines, imports of `api_services/` or
`background_jobs/`.
**Severity**: 🟠 High

### V-M3 · Flask context access in models

**Pattern**: `from flask import current_app, g, request` in a model file.
**Severity**: 🔴 Critical (models must be framework-agnostic)

### V-M4 · `db.session.commit()` inside model methods

**Pattern**: A model method calls `db.session.commit()` directly.
**Detection**: `.commit()` in a model file.
**Severity**: 🟠 High (commit belongs in services or route-level transaction management)

---

## 3. Service Violations (`db/services/`)

### V-S1 · Services importing from routes

**Pattern**: `from main_app.public` import in a service file.
**Severity**: 🔴 Critical (inverted dependency)

### V-S2 · HTTP response construction in services

**Pattern**: `jsonify(...)`, `make_response(...)`, or `abort(...)` called inside
a service.
**Detection**: Import of `flask` response utilities in service files.
**Severity**: 🟠 High

### V-S3 · Services importing other services in a chain >2 deep

**Pattern**: ServiceA → ServiceB → ServiceC indicates missing abstraction.
**Detection**: Transitive import graph of services longer than 2 hops.
**Severity**: 🟡 Medium

---

## 4. Core / Utils Violations (`core/`, `utils/`)

### V-C1 · Flask context dependency in core utilities

**Pattern**: `current_app`, `g`, `request` used in `core/` or `utils/` without
explicit documentation that the function requires app context.
**Severity**: 🟠 High

### V-C2 · Database access in core utilities

**Pattern**: ORM queries or `db.session` usage in `core/` or `utils/`.
**Severity**: 🔴 Critical

### V-C3 · Business logic in `core/crypto.py` or `core/cookies.py`

**Pattern**: Domain-specific decisions (e.g., "if user is admin, sign differently")
inside what should be a pure cryptographic utility.
**Severity**: 🟡 Medium

---

## 5. Config Violations (`config/`)

### V-CF1 · Instantiation in config files

**Pattern**: Object construction (`MyService()`, `db.create_engine(...)`) inside
`config/classes.py` or `config/flask_config.py`.
**Severity**: 🟠 High

### V-CF2 · Business logic in config

**Pattern**: Conditional logic that applies domain rules inside config.
**Severity**: 🟠 High

### V-CF3 · Environment-specific code scattered outside config

**Pattern**: `os.getenv(...)` calls outside of `config/` (except `app.py`).
**Detection**: `os.getenv` or `os.environ` in model/service/route files.
**Severity**: 🟡 Medium

---

## 6. Background Job Violations (`background_jobs/`)

### V-BG1 · Workers importing from routes

**Pattern**: `from main_app.public` in any worker.
**Severity**: 🔴 Critical

### V-BG2 · HTTP request/response handling inside workers

**Pattern**: `requests.get/post` for internal app endpoints (workers should call
services directly, not HTTP).
**Severity**: 🟠 High

### V-BG3 · Missing app context push in workers

**Pattern**: Workers that access `db.session` or `current_app` without
`app.app_context()` or a context manager.
**Detection**: `db.session` used without nearby `with app.app_context()`.
**Severity**: 🔴 Critical

---

## 7. API Services Violations (`api_services/`)

### V-API1 · Database access in API service layer

**Pattern**: ORM queries inside `api_services/`.
**Severity**: 🔴 Critical (api_services are for external HTTP only)

### V-API2 · Business logic in API services

**Pattern**: Domain decisions (pricing, permissions, status changes) inside
what should be a thin HTTP client wrapper.
**Severity**: 🟠 High

---

## 8. Extensions Violations (`extensions.py`)

### V-EX1 · Configuration logic in extensions

**Pattern**: Conditional setup, environment reading, or object wiring in
`extensions.py` beyond bare `ext = ExtensionClass()` calls.
**Severity**: 🟡 Medium

---

## 9. Cross-Cutting Violations

### V-X1 · Circular imports

**Pattern**: Module A imports Module B which imports Module A (directly or transitively).
**Detection**: Use `python -c "import main_app"` and catch `ImportError`; or trace
imports manually.
**Severity**: 🟠 High

### V-X2 · God modules

**Pattern**: A single file contains >300 lines and mixes multiple responsibilities.
**Severity**: 🟡 Medium

### V-X3 · Shared mutable state outside of proper abstractions

**Pattern**: Module-level mutable variables (lists, dicts) modified by multiple layers.
**Detection**: Module-level variable assignment followed by `.append`/`.update` in
functions across different files.
**Severity**: 🟠 High
