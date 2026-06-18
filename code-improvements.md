# Code Improvement Plan

## Overview

Address critical and high-severity findings across security, architecture, and code
quality. Each section is self-contained and can be implemented independently.

---

## 1. Security: Fix Path Traversal in Explorer Routes (CRITICAL)

**Files:**

-   `src/main_app/app_routes/main_routes/explorer_routes.py` (lines 122-135, 138-168)
-   `src/main_app/app_routes/utils/explorer_utils.py` (add `_validate_path_under_base` to `__all__`)

**Problem:** `serve_media()` and `serve_thumb()` construct `dir_path = svg_data_path / title_dir / subdir` with no path
validation. An attacker can pass `../` in `title_dir` or `subdir` to read arbitrary files.

**Fix:** Reuse `_validate_path_under_base()` from `explorer_utils.py`:

```python
# In serve_media() and serve_thumb(), replace:
dir_path = svg_data_path / title_dir / subdir
dir_path = str(dir_path.absolute())

# With:
from ..utils.explorer_utils import _validate_path_under_base
try:
    dir_path = _validate_path_under_base(title_dir, subdir)
except PermissionError:
    abort(403)
dir_path = str(dir_path)
```

---

## 2. Security: Fix Path Traversal in load_job_result (MEDIUM-HIGH)

**File:** `src/main_app/su_services/jobs_files_service.py` (lines 69-74, and same pattern in
`is_job_cancelled_file_exist`, `create_job_cancelled_file`)

**Problem:** `result_file = jobs_dir / result_file` concatenates user-controlled path segments without validation.

**Fix:** Extract a shared `_safe_job_path(filename)` helper, then use it in all three functions:

```python
def _safe_job_path(filename: str) -> Path:
    jobs_dir = get_jobs_data_dir()
    candidate = (jobs_dir / filename).resolve()
    if jobs_dir not in candidate.parents and candidate != jobs_dir:
        raise ValueError(f"Path traversal blocked: {candidate}")
    return candidate
```

---

## 3. Security: Remove `|safe` from card_header Macro (LOW-MEDIUM)

**File:** `src/templates/_macros.html` (line 72)

**Problem:** `{{ title|safe }}` could cause XSS if any caller passes user-controlled data. Currently safe
because callers pass static strings, but the macro is a latent risk.

**Fix:** Remove `|safe` — Flask auto-escapes by default:

```jinja2
- <h5 class="mb-0">{{ title|safe }}</h5>
+ <h5 class="mb-0">{{ title }}</h5>
```

---

## 4. Architecture: Resolve Circular Dependency (CRITICAL)

**Files:**

-   `src/main_app/su_services/auth_service.py` (imports from `..app_routes.auth.oauth`)
-   `src/main_app/app_routes/auth/oauth.py` (defines `complete_login`, `start_login`, `OAuthIdentityError`)
-   `src/main_app/app_routes/auth/routes.py` (imports from both)

**Problem:** `su_services/auth_service.py` imports from `app_routes/auth/oauth.py` — a back-dependency where
the service layer depends on the route layer.

**Fix:** Move `oauth.py` from `app_routes/auth/` into `su_services/`:

1. Move `src/main_app/app_routes/auth/oauth.py` → `src/main_app/su_services/mwoauth_handshake.py`
2. Update import in `su_services/auth_service.py`: `from .mwoauth_handshake import complete_login`
3. Update import in `app_routes/auth/routes.py`: `from ...su_services.mwoauth_handshake import OAuthIdentityError, start_login`
4. Add `OAuthIdentityError`, `start_login`, `complete_login` to `su_services/__init__.py` exports

---

## 5. Architecture: Deduplicate Job Route Logic (CRITICAL)

**Files:**

-   `src/main_app/app_routes/public_jobs.py` (~250 lines, remove 5 duplicated handler functions)
-   `src/main_app/app_routes/admin_routes/jobs.py` (~250 lines, same removals)
-   `src/main_app/app_routes/jobs_routes_utils.py` (add the 5 shared handler functions)

**Problem:** 95% identical copy-paste between the two route files. The only difference is the
`JOBS_BP` constant and `@admin_required` on admin routes.

**Fix:** Move handlers into `jobs_routes_utils.py` parameterized by `bp_name`:

-   `cancel_job_handler(job_id, job_type, bp_name)` → moved from both files
-   `delete_job_handler(job_id, job_type, bp_name)` → moved from both files
-   `start_job_handler(job_type, args, bp_name)` → moved from both files
-   `jobs_list_handler(job_type, template_data, bp_name)` → moved from both files
-   `job_detail_handler(job_id, job_type, template_data, bp_name, expand_all=False)` → moved from both files

`@admin_required` stays on the route decorators in `_setup_routes()` — the shared handler
functions don't need it.

---

## 6. Architecture: Move Blueprint Registration into Factory (HIGH)

**Files:**

-   `src/main_app/app_routes/admin/routes.py` (line 86 — remove module-level `register_blueprints(bp_admin)`)
-   `src/main_app/app_routes/__init__.py` (call the registration function from factory)

**Problem:** Blueprint sub-registration happens at import time via `register_blueprints(bp_admin)` at the
bottom of `admin/routes.py`, before `create_app()` finishes.

**Fix:**

1. Remove the module-level `register_blueprints(bp_admin)` call from `admin/routes.py`
2. Rename the local function to `_register_admin_sub_blueprints(bp_admin)`
3. Call it from `app_routes/__init__.py`'s `register_blueprints(app)` after registering `bp_admin`

---

## 7. Code Quality: Add `from __future__ import annotations` (HIGH)

**Files missing it (15):**

-   `src/main_app/db/templates_utils.py`
-   `src/main_app/shared/decode_bytes.py`
-   `src/main_app/app_routes/utils/compare.py`
-   `src/main_app/app_routes/utils/explorer_utils.py`
-   `src/main_app/app_routes/utils/thumbnail_utils.py`
-   `src/main_app/utils/wikitext/temp_source.py`
-   `src/main_app/utils/wikitext/temps_bot.py`
-   `src/main_app/utils/wikitext/owid_sliders_rcs/main_file.py`
-   `src/main_app/jobs_workers/objects.py`
-   `src/main_app/jobs_workers/utils/__init__.py`
-   `src/main_app/api_services/category.py`
-   `src/offline/sitemap.py`
-   `_works_files/add_all.py`
-   `_works_files/z2.py`
-   `_works_files/tree.py`
-   `_works_files/tests_dirs.py`

**Fix:** Add `from __future__ import annotations` as the first import in each file.

---

## 8. Code Quality: Narrow Broad Exception Handling (HIGH)

| File                                          | Fix                                                                       |
| --------------------------------------------- | ------------------------------------------------------------------------- |
| `db/services/admin_service.py:24`             | `except Exception` → `except (ValueError, LookupError, OperationalError)` |
| `db/services/settings_service.py:108`         | `except Exception` → `except (ValueError, OperationalError)`              |
| `su_services/jobs_files_service.py:80`        | `except Exception` → `except (OSError, json.JSONDecodeError)`             |
| `app_routes/public_jobs.py` lines 62,69       | Remove bare `except Exception` — use specific exceptions                  |
| `app_routes/admin_routes/jobs.py` lines 62,69 | Same as public_jobs.py                                                    |
| `app_routes/profile.py:37`                    | `except Exception` → `except (ValueError, OperationalError)`              |

---

## 9. Code Quality: Deduplicate start_job / start_job_cli (HIGH)

**File:** `src/main_app/jobs_workers/jobs_worker.py`

**Problem:** `start_job()` and `start_job_cli()` share ~80% identical code. The only difference is
`daemon=True` and `app=app or current_app._get_current_object()`.

**Fix:** Extract `_start_job_impl()`:

```python
def _start_job_impl(user, job_type, args=None, *, daemon=False, flask_app=None) -> int:
    # Shared: job_data lookup, job creation, thread spawning
    ...

def start_job(user, job_type, args=None) -> int:
    return _start_job_impl(user, job_type, args, daemon=True,
                           flask_app=current_app._get_current_object())

def start_job_cli(user, job_type, args=None, app=None) -> int:
    return _start_job_impl(user, job_type, args,
                           flask_app=app or current_app._get_current_object())
```

---

## 10. Architecture: Fix Teardown Function (MEDIUM)

**File:** `src/main_app/__init__.py` (lines 117-125)

**Problem:** `_cleanup_connections` has an entirely commented-out body, only `pass` remains.

**Fix:** Replace `pass` with `db.session.remove()` for proper session cleanup in background threads.

---

## 11. Testing: Fix Meaningless Assertions (MEDIUM)

**Files:**

-   `tests/unit/jobs_workers/admin_jobs_workers/test_jobs_worker.py` — remove `assert start_job is start_job` (always True)
-   `tests/unit/core/test_cookies.py` — replace `assert issubclass(CookieHeaderClient, object)` with `assert issubclass(CookieHeaderClient, FlaskClient)`

---

## 12. Testing: Write Tests for delete_service.py (MEDIUM)

**File:** `src/main_app/db/services/delete_service.py` — 9 functions with zero test coverage.

**Fix:** Create `tests/unit/db/services/test_delete_service.py` using the existing `setup_db` conftest fixture:

-   `delete_record_by_pk` — deletes by primary key, handles non-existent records
-   `delete_user` — cascades through related records
-   `delete_job` — removes job from DB, handles integrity errors
-   All other `delete_*` functions with edge cases

---

## Verification

```bash
black src/ tests/
isort src/ tests/
pytest -v -m "not network"
python -c "from src.main_app import create_app"  # no circular imports
```

Key checks:

1. All non-network tests pass
2. No circular import errors at startup
3. Path traversal attempts on `/explorer/media/../../../etc/passwd/files/test.svg` return 403
4. Job cancellation/deletion works identically for both public and admin routes
5. OAuth login flow still works end-to-end
