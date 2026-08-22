# Plan 004: Add global response-hardening headers

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 8bf215bc..HEAD -- src/main_app/__init__.py`

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: security
- **Planned at**: commit `8bf215bc`, 2025-08-11

## Why this matters

Security response headers (`Content-Security-Policy`, `X-Content-Type-Options`,
`X-Frame-Options`, `Referrer-Policy`) are currently set manually on individual
file-serving routes (`explorer_routes.py`, `jobs_utils_bp.py`) but not applied
globally. Routes that don't set these headers are vulnerable to MIME-sniffing
attacks, clickjacking, and content injection. A single `@app.after_request` hook
ensures every response gets hardened headers, closing the gaps.

## Current state

- `src/main_app/__init__.py` — application factory, the right place for a global hook
  - The `create_app()` function (lines 110-166) already has `@app.context_processor` and error handlers
  - Currently no `@app.after_request` hook exists

- Headers are set manually on ~5 individual routes:
  - `src/main_app/public/main_routes/explorer_routes.py:135-136` (CSP + nosniff on `serve_media`)
  - `src/main_app/public/main_routes/explorer_routes.py:156-157` (CSP + nosniff on `serve_thumb`)
  - `src/main_app/public/jobs_utils_bp.py:56-57,78-79,88-89` (CSP + nosniff on file-serving routes)

- Routes that currently lack headers: all HTML pages, the API JSON endpoints,
  the auth routes, the inject/extract routes, etc.

Repo convention: the app factory pattern is used (`create_app()` in `__init__.py`).
Global hooks go in the factory. See the existing error handlers (lines 30-106)
as the pattern.

## Commands you will need

| Purpose   | Command                                              | Expected on success           |
|-----------|------------------------------------------------------|-------------------------------|
| Tests     | `python3 -m pytest tests/ -x -q -m "not network"`   | all pass                      |
| Grep      | `grep -n "after_request" src/main_app/__init__.py`  | one match (the new hook)      |

## Scope

**In scope**:
- `src/main_app/__init__.py` — add `@app.after_request` hook
- `tests/integration/test_app_factory_regression.py` — add/update header assertion test

**Out of scope**:
- Do NOT remove per-route header assignments in `explorer_routes.py` or `jobs_utils_bp.py` — they override the global defaults with stricter CSP for SVG content. Leave them as-is.
- Do NOT modify nginx/proxy configuration (out of repo scope).

## Steps

### Step 1: Add `@app.after_request` hook in `create_app()`

In `src/main_app/__init__.py`, inside the `create_app()` function, add a new
`@app.after_request` handler after the error handlers (after line 106, before
`init_app_and_db`). Add it inside `create_app()` so it has access to `app`:

```python
    @app.after_request
    def add_security_headers(response):
        """Add security headers to every response."""
        # Only set if not already set by a route-specific handler
        if "X-Content-Type-Options" not in response.headers:
            response.headers["X-Content-Type-Options"] = "nosniff"
        if "X-Frame-Options" not in response.headers:
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
        if "Content-Security-Policy" not in response.headers:
            response.headers["Content-Security-Policy"] = "default-src 'self'"
        if "Referrer-Policy" not in response.headers:
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response
```

The `if not in headers` pattern ensures route-specific handlers (like the
stricter CSP on SVG file serving) take precedence.

**Verify**: `grep -n "after_request" src/main_app/__init__.py` → shows one match

### Step 2: Run the test suite

**Verify**: `python3 -m pytest tests/ -x -q -m "not network"` → all pass

### Step 3: Add a regression test

In `tests/integration/test_app_factory_regression.py`, add a test that verifies
security headers are present on a basic response:

```python
def test_security_headers_on_html_response(mock_client):
    """Security headers should be present on all HTML responses."""
    response = mock_client.get("/")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert "Content-Security-Policy" in response.headers
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
```

**Verify**: `python3 -m pytest tests/integration/test_app_factory_regression.py -x -q -m "not network"` → passes

## Test plan

- New test: `test_security_headers_on_html_response` — verifies headers on `GET /`
- Existing test: `tests/integration/test_app_factory_regression.py` may already test basic app responses; extend it
- Verification: `python3 -m pytest tests/ -x -q -m "not network"` → all pass

## Done criteria

- [ ] `grep -n "after_request" src/main_app/__init__.py` shows one match
- [ ] `GET /` returns `X-Content-Type-Options: nosniff` header
- [ ] `GET /` returns `X-Frame-Options: SAMEORIGIN` header
- [ ] `GET /` returns `Content-Security-Policy` header
- [ ] `GET /` returns `Referrer-Policy` header
- [ ] `python3 -m pytest tests/ -x -q -m "not network"` exits 0
- [ ] No files outside the in-scope list are modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

- An `@app.after_request` hook already exists in `create_app()`.
- Adding the hook causes test failures that can't be resolved without modifying out-of-scope files.
- The CSP `default-src 'self'` breaks inline scripts in templates — if this happens, widen to `default-src 'self' 'unsafe-inline'` and report the issue.

## Maintenance notes

- If CSP needs to be widened for specific pages (e.g., inline scripts in Jinja templates), use route-specific overrides with the existing pattern (`response.headers["Content-Security-Policy"] = "..."`).
- The `X-Frame-Options: SAMEORIGIN` may need to be `DENY` if the app should never be embedded. Discuss with the maintainer.
- If the app is served behind a reverse proxy that already sets these headers, the `if not in headers` guard prevents duplicates.
