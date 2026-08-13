# Codebase Audit Report — SVG Translate Web

**Generated**: 2025-08-11
**Commit**: `8bf215bc` (branch `oo`, identical to `main`)
**Auditor**: improve skill (senior advisor, read-only)
**Effort level**: standard (full-repo, all categories)

---

## Executive Summary

The SVG Translate Web application is a well-structured Flask app for copying SVG translations between language versions on Wikimedia Commons. The codebase follows good conventions (factory pattern, Blueprints, service layer, base worker abstraction) and has substantial test coverage (~200 test files, both unit and integration).

The audit identified **12 findings** across security, correctness, performance, tech debt, and DX. Six findings were promoted to implementation plans in `plans/`. The remaining six were assessed as low-priority or trivial to fix and are recorded in the "Rejected Findings" section below.

### Top risks

1. **Security**: Unauthenticated API endpoints expose internal operational data; `/owidcharts/all` exposes unpublished charts.
2. **Security**: Custom in-memory rate limiter doesn't scale across gunicorn/uvicorn workers, making auth rate limiting ineffective in production.
3. **Security**: `DevelopmentConfig` ships with `TESTING = True`, disabling Flask safety nets if accidentally deployed.
4. **DX**: Python version mismatch (`pyproject.toml` requires ≥3.13, runtime is 3.12).

---

## Scope

### Audited

- All Python source under `src/main_app/` (200 files, ~20,500 lines)
- Test suite structure and fixtures (`tests/`, 200 files, ~32,000 lines)
- Configuration (`pyproject.toml`, `requirements.txt`, `.env.example`, `pytest.ini`)
- CI configuration (`.github/workflows/`)
- Application factory, auth flow, job worker system, database layer, API routes
- Git history (last 30 commits)

### Not audited

- `CopySVGTranslation` third-party package (external dependency)
- `MagicMock/` directory (test artifacts)
- `_works_files/` (offline CLI tools, explicitly excluded from Flask app)
- Frontend JavaScript or CSS
- Jinja2 templates (XSS via template rendering not deeply audited)
- Production Toolforge deployment configuration

---

## Recon Facts

| Property | Value |
|----------|-------|
| Language | Python 3.12.3 (runtime), 3.13 declared in pyproject.toml |
| Framework | Flask 3.x + Flask-SQLAlchemy + Flask-Migrate |
| Database | MySQL (pymysql) in production, SQLite in-memory for tests |
| Package manager | pip (requirements.txt) |
| Test framework | pytest (~200 test files, unit + integration + network markers) |
| Formatter | Black (line-length: 120) |
| Linter | Ruff (line-length: 120) |
| Type checker | mypy + pyright (both configured but not enforced in CI) |
| CI | GitHub Actions — only `opencode` bot workflow, no automated test/lint pipeline |
| Deployment | Wikimedia Toolforge (gunicorn/uvicorn) |
| Auth | MediaWiki OAuth via mwoauth + Fernet-encrypted session cookies |
| Background jobs | Threading-based workers with `BaseObjectsJobWorker` pattern |
| Rate limiting | Custom in-memory `RateLimiter` class (flask-limiter in requirements but unused) |

---

## Findings Table

Findings ordered by leverage (impact ÷ effort, discounted by confidence).

| # | Finding | Category | Impact | Effort | Risk | Confidence | Evidence | Planned? |
|---|---------|----------|--------|--------|------|------------|----------|----------|
| 1 | Unauthenticated `/api/` endpoints expose internal data | Security | M | S | LOW | HIGH | `src/main_app/public/api_routes.py:18-20` | ✅ 002 |
| 2 | `/owidcharts/all` exposes unpublished charts without auth | Security | M | S | LOW | HIGH | `src/main_app/public/main_routes/owid_charts_routes.py:40-44` | ✅ 002 |
| 3 | In-memory rate limiter is per-process, doesn't scale | Security | M | M | LOW | HIGH | `src/main_app/public/auth/rate_limit.py:13-49` | ✅ 006 |
| 4 | `DevelopmentConfig` has `TESTING = True` | Security | M | S | LOW | HIGH | `src/main_app/config/flask_config.py:117` | ✅ 001 |
| 5 | `read_job_result_file` lacks ownership check (IDOR) | Security | L | S | LOW | MED | `src/main_app/public/shared_jobs_routes.py:338-342` | ❌ (see note) |
| 6 | Python version mismatch: pyproject.toml vs runtime | DX | M | S | LOW | HIGH | `pyproject.toml:6` vs `python3 --version` → 3.12.3 | ✅ 003 |
| 7 | 19 source files missing `from __future__ import annotations` | Tech Debt | L | S | LOW | HIGH | grep across `src/main_app/` | ❌ |
| 8 | `jobs_service.py` duplicates ~80% of stats query code | Tech Debt | L | S | LOW | HIGH | `jobs_service.py:68-120` vs `:270-302` | ✅ 005 |
| 9 | Mixed SQLAlchemy 1.x and 2.0 APIs in `CRUDService` | Tech Debt | M | M | MED | HIGH | `crud_service.py:66-74` vs `:82-102` | ❌ |
| 10 | `create_helper.py` uses f-string SQL in `text()` | Correctness | L | S | LOW | MED | `create_helper.py:45` | ❌ |
| 11 | `compare` route lacks path traversal validation | Security | L | S | LOW | MED | `explorer_routes.py:160-170` | ❌ |
| 12 | `serve_thumb` generates thumbnails on-demand without throttling | Perf/Security | M | M | MED | MED | `explorer_routes.py:145-153` | ❌ |

---

## Finding Details

### Finding 1: Unauthenticated API endpoints [HIGH confidence]

**Evidence**: `src/main_app/public/api_routes.py:18-20`

The `/api/templates`, `/api/templates-mismatched-years`, and `/api/templates-need-update` endpoints have no authentication decorators. They expose internal template metadata, file relationships, and operational statistics.

While the underlying data originates from public Wikimedia Commons pages, the aggregated structure and internal relationships constitute operational data that should require at least login authentication.

**Impact**: Anonymous users can enumerate all templates, identify mismatched years, and discover which templates need updates — information useful for targeted attacks on the wiki infrastructure.

**Plan**: `plans/002-protect-api-and-unpublished-data.md`

---

### Finding 2: `/owidcharts/all` exposes unpublished charts [HIGH confidence]

**Evidence**: `src/main_app/public/main_routes/owid_charts_routes.py:40-44`

The `index()` route correctly filters to `is_published` charts, but the `all_charts()` route returns ALL charts (including unpublished) with no authentication. The route is publicly accessible.

```python
# Line 40-44 — no filter, no auth
def all_charts(self) -> str:
    charts_with_templates = self.charts_and_tmps_service.list_all()
    charts = [x.to_dict_joined() for x in charts_with_templates]
    # Returns ALL charts including unpublished
```

**Impact**: Unpublished chart metadata is exposed to the public internet.

**Plan**: `plans/002-protect-api-and-unpublished-data.md`

---

### Finding 3: In-memory rate limiter doesn't scale [HIGH confidence]

**Evidence**: `src/main_app/public/auth/rate_limit.py:13-49`

The custom `RateLimiter` class stores request timestamps in a Python dict in the current process. With gunicorn/uvicorn running multiple workers (standard on Toolforge), each worker maintains independent rate limit state. An attacker distributing requests across workers effectively multiplies their rate limit budget by the number of workers.

`flask-limiter` is listed in `requirements.txt` but completely unused.

**Impact**: Authentication rate limiting is ineffective in multi-worker production deployments, leaving OAuth login/callback endpoints vulnerable to brute-force attacks.

**Plan**: `plans/006-replace-custom-rate-limiter.md`

---

### Finding 4: `DevelopmentConfig` has `TESTING = True` [HIGH confidence]

**Evidence**: `src/main_app/config/flask_config.py:117`

```python
class DevelopmentConfig(Config):
    DEBUG: bool = True
    TESTING: bool = True  # <-- disables error handlers, CSRF edge cases
```

Flask's `TESTING` mode disables error handlers, propagates exceptions, and can disable CSRF protection. If the app is accidentally deployed with `FLASK_ENV=development` (the default in `.env.example`), production safety nets are disabled.

**Impact**: Accidental deployment with development config exposes stack traces and disables security features.

**Plan**: `plans/001-fix-dev-config-testing-flag.md`

---

### Finding 5: `read_job_result_file` lacks ownership check (IDOR) [MED confidence]

**Evidence**: `src/main_app/public/shared_jobs_routes.py:338-342`

```python
def read_job_result_file(self, result_file: str, job_type: str) -> ResponseReturnValue:
    if job_type not in self.jobs_data_infos:
        abort(404)
    result_data = load_job_result(result_file)
    return jsonify(result_data)
```

This endpoint requires `user_login_required` but doesn't verify that the requesting user owns the job whose result file they're reading. Any authenticated user who guesses or discovers a result filename can read another user's job results.

**Impact**: Information disclosure — job results may contain usernames, file lists, and error details from other users' operations.

**Mitigation note**: The result filenames are not easily guessable (they include job IDs and timestamps), but this should still be fixed. Not planned as a standalone fix because the impact is limited and the fix requires changes to the job result storage pattern.

---

### Finding 6: Python version mismatch [HIGH confidence]

**Evidence**: `pyproject.toml:6` declares `requires-python = ">=3.13"`, but runtime is Python 3.12.3.

All tool configurations (black, ruff, mypy, pyright) target Python 3.13, potentially flagging valid 3.12 code or missing 3.12-specific issues. `AGENTS.md` states "Python 3.11+" which contradicts both.

**Impact**: Potential installation failures, incorrect linting/type-checking results, and confusion for new contributors.

**Plan**: `plans/003-fix-python-version-mismatch.md`

---

### Finding 7: Missing `from __future__ import annotations` in 19 files [HIGH confidence]

**Evidence**: 153 of 172 non-init Python files in `src/main_app/` include the import. 19 files don't, including `compare.py`, `explorer_utils.py`, `category.py`, `service.py`, and others.

**Impact**: Inconsistent behavior for type annotations (some files use postponed evaluation, others don't). Minor maintenance burden.

**Fix**: A single `ruff --fix` pass or manual sweep. Not worth a dedicated plan.

---

### Finding 8: Duplicated job stats queries in `JobsService` [HIGH confidence]

**Evidence**: `src/main_app/database/services/jobs_service.py`

`get_user_jobs_stats` (lines 68-120) and `_get_all_user_jobs_stats` (lines 270-302) share ~80% identical code. The only difference is an optional `jobs_types` filter. `get_user_jobs_stats` already delegates to `_get_all_user_jobs_stats` when `jobs_types` is None.

**Impact**: Bug fixes or feature changes must be made in two places. Risk of divergence.

**Plan**: `plans/005-deduplicate-jobs-service-queries.md`

---

### Finding 9: Mixed SQLAlchemy 1.x and 2.0 APIs in `CRUDService` [HIGH confidence]

**Evidence**: `src/main_app/database/services/crud_service.py`

`list_all()` uses legacy `session.query()` (SQLAlchemy 1.x):
```python
stmt = self.session.query(self.model)
```

`list()` uses modern `session.execute(select())` (SQLAlchemy 2.0):
```python
stmt = self._base_select()
result = self.session.execute(stmt).scalars().all()
```

**Impact**: Not broken today (Flask-SQLAlchemy supports both), but creates maintenance confusion and will require migration when SQLAlchemy removes the legacy API.

**Recommendation**: Plan a future migration to fully adopt SQLAlchemy 2.0 style. Not urgent.

---

### Finding 10: f-string SQL in `create_helper.py` [MED confidence]

**Evidence**: `src/main_app/database/create_helper.py:45`

```python
conn.execute(text(f"DROP VIEW IF EXISTS {table.name}"))
```

`table.name` comes from SQLAlchemy model metadata, not user input, so this is not exploitable via SQL injection. However, it sets a bad pattern precedent.

**Impact**: Low — not exploitable. A future cleanup can switch to parameterized queries.

---

### Finding 11: `compare` route lacks path traversal validation [MED confidence]

**Evidence**: `src/main_app/public/main_routes/explorer_routes.py:160-170`

The `compare()` route constructs file paths from URL parameters without the `is_relative_to()` validation used in `serve_media()` and `serve_thumb()`. However, the impact is limited because `analyze_file()` only parses XML (doesn't serve files to the client) and the route requires authentication via the blueprint's before_request hook.

**Impact**: Low — XML parsing only, no file content served.

---

### Finding 12: On-demand thumbnail generation without throttling [MED confidence]

**Evidence**: `src/main_app/public/main_routes/explorer_routes.py:145-153`

`serve_thumb()` triggers `save_thumb()` on every cache miss. An attacker could request many unique thumbnails to cause CPU/disk pressure. The risk is mitigated by the fact that thumbnails are cached after first generation.

**Impact**: Medium — DoS via CPU exhaustion during thumbnail generation. Mitigated by caching.

**Recommendation**: Consider pre-generating thumbnails during job execution, or adding a size limit / rate limit to the thumbnail endpoint.

---

## Direction Findings

Forward-looking suggestions grounded in the codebase, separate from the bug/debt table above.

### A. Adopt `flask-limiter` with shared backend (see Plan 006)

`flask-limiter` is already in `requirements.txt`. Switching from the custom in-memory rate limiter to `flask-limiter` with a Redis backend would make rate limiting effective across multiple workers. This is the most impactful infrastructure improvement for the auth layer.

### B. Migrate `CRUDService` to SQLAlchemy 2.0

Consolidating on `select()` + `session.execute()` across all CRUD methods would eliminate the mixed-API confusion and prepare for SQLAlchemy 3.0. Effort: M. Best done as a focused refactoring sprint.

### C. Add global security headers via `@app.after_request` (see Plan 004)

Security headers are currently set manually on individual file-serving routes. A single `@app.after_request` hook would ensure all responses get hardened headers.

### D. Consolidate job worker result objects

Multiple workers define their own result object classes (`CropMainFilesWorkerObject`, `CopySvgLangsWorkerObject`, etc.) with slight variations in field names and structure. A unified `JobResult` base class would reduce boilerplate, make templates more uniform, and simplify the result-loading API.

---

## Rejected Findings

These were considered during the audit but judged not worth dedicated implementation plans:

| Finding | Rejection reason |
|---------|-----------------|
| Stale `.pyc` cache file for deleted `translate_routes.py` | Trivial: `find . -name "*.pyc" -delete`. Add to `.gitignore`. |
| `create_helper.py` f-string SQL | `table.name` from SQLAlchemy metadata — not exploitable. |
| `compare` route path traversal | Only parses XML, doesn't serve files. Low impact. |
| Missing `from __future__ import annotations` (19 files) | Sweep with ruff. Not worth a plan. |
| Mixed SQLAlchemy 1.x/2.0 APIs | Medium-term migration, not urgent. |
| `serve_thumb` thumbnail DoS | Mitigated by caching. Future improvement. |
| `read_job_result_file` IDOR | Limited impact (filenames not easily guessable). Fix alongside result storage refactor. |

---

## Plans Generated

Six implementation plans have been written to `plans/`:

| Plan | Title | Priority | Effort | Category |
|------|-------|----------|--------|----------|
| 001 | Remove `TESTING = True` from DevelopmentConfig | P1 | S | security |
| 002 | Protect API endpoints and unpublished chart data | P1 | M | security |
| 003 | Fix Python version mismatch in pyproject.toml | P2 | S | dx |
| 004 | Add global response-hardening headers | P1 | S | security |
| 005 | Deduplicate job stats query methods in JobsService | P2 | S | tech-debt |
| 006 | Replace custom in-memory rate limiter with flask-limiter | P2 | M | security |

Each plan is self-contained with:
- Exact file paths and line numbers
- Current-state code excerpts
- Step-by-step instructions with verification commands
- Test plan and done criteria
- STOP conditions for the executor
- Maintenance notes for future reviewers

### Recommended execution order

**Quick wins** (can be parallelized): 001 → 004 → 003 → 005

**Then**: 002 (API auth) → 006 (rate limiter migration)

Plans 001, 003, 004 are independent S-effort changes with LOW risk. Plans 002 and 006 are M-effort but still independent of each other.

---

## Appendix: Key Architecture Observations

### Strengths
- Clean application factory pattern with proper extension initialization
- Well-organized Blueprint structure separating admin/public/API routes
- Robust job worker system with cancellation support (local + DB + file-based)
- Comprehensive test suite with unit/integration/network markers
- Proper OAuth state verification with Fernet-signed tokens
- CSRF protection enabled globally

### Areas for future improvement
- No CI pipeline for automated testing/linting (only `opencode` bot workflow)
- No database migration files (tables created via `create_all` at startup)
- Threading-based job workers could benefit from a task queue (Celery/RQ) for production scale
- Multiple DB session patterns (`CRUDService` vs `JobsService` vs direct `db.session`)
- `AGENTS.md` and `CLAUDE.md` have some stale information (Python version, file paths)
