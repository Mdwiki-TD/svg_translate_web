# AGENTS.md

Guidelines for AI agents working in this SVG Translate Web repository.

## Project Overview

Flask-based web application for copying SVG translations between language versions on Wikimedia Commons. Runs on Wikimedia Toolforge with MediaWiki OAuth authentication.

## Build/Test Commands

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run the application
python -m flask --app src.app run
python src/app.py debug  # Debug mode

# Testing
pytest                           # Run all tests
pytest tests/test_file.py       # Run specific test file
pytest tests/test_file.py::test_func  # Run single test
pytest -m "not network"         # Skip network tests
pytest --cov=src                # Run with coverage

# Code formatting
black .                         # Format code (line length: 120)
isort .                         # Sort imports
```

## Code Style Guidelines

### Python Style

-   **Line length**: 120 characters (configured in pyproject.toml)
-   **Target version**: Python 3.11+
-   **Formatter**: Black
-   **Import sorter**: isort (profile: black)

### Imports

Use `from __future__ import annotations` at the top of all Python files. Follow this import order:

1. Future imports
2. Standard library imports
3. Third-party library imports
4. Local application imports

Example:

```python
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import pymysql
from flask import Flask

from .config import settings
from .utils.verify import verify_required_fields
```

### Naming Conventions

-   **Classes**: `PascalCase` (e.g., `TaskStorePyMysql`, `DbConfig`)
-   **Functions/Methods**: `snake_case` (e.g., `get_settings`, `format_task`)
-   **Variables**: `snake_case` (e.g., `task_id`, `file_name`)
-   **Constants**: `UPPER_SNAKE_CASE` (e.g., `TASK_STORE`, `MAX_RETRIES`)
-   **Private**: prefix with `_` (e.g., `_load_db_data`, `_cleanup_connections`)

### Type Hints

Use type hints throughout. Use `|` for union types (Python 3.11+):

```python
def get_page_text(file_name: str, site: mwclient.Site | None) -> str:
    ...
```

### Docstrings

Use Google-style docstrings with Args/Returns sections:

```python
def format_stage_timestamp(value: str) -> str:
    """Format ISO8601 like '2025-10-27T04:41:07' to 'Oct 27, 2025, 4:41 AM'.

    Args:
        value: ISO8601 timestamp string.

    Returns:
        Formatted timestamp string or empty string if parsing fails.
    """
```

### Error Handling

-   Use specific exceptions and log with `logger.exception()` for stack traces
-   Return meaningful error dictionaries: `{"success": False, "error": "message"}`
-   Use validation helpers like `verify_required_fields()`
-   Handle exceptions gracefully, never expose sensitive info

Example:

```python
try:
    page = site.pages[file_name]
    return page.text()
except Exception as exc:
    logger.exception(f"Failed to retrieve wikitext for {file_name}", exc_info=exc)
    return ""
```

### Flask Patterns

-   Use Blueprints for route organization
-   Use application factory pattern (`create_app()`)
-   Register error handlers for 400, 403, 404, 405, 500, CSRFError
-   Use `@lru_cache` for expensive configuration loading

### Database

-   Use parameterized queries with `%s` placeholders
-   Always close connections in teardown handlers
-   Use retry logic for transient failures
-   Lazy import DB modules to avoid circular dependencies

### Logging

-   Use module-level loggers: `logger = logging.getLogger(__name__)`
-   Use f-strings for dynamic content
-   Use appropriate levels: debug, info, warning, error, exception

## Project Structure

```
src/
  main_app/
    __init__.py          # Flask app factory
    config.py            # Settings dataclasses
    app_routes/          # Flask blueprints
      admin/             # Admin panel (sidebar, routes, auth)
      admin_routes/      # Admin sub-routes (coordinators, jobs, etc.)
      auth/              # OAuth authentication
      main_routes/       # Public routes
    api_services/        # MediaWiki API clients
      clients/           # mwclient site builders (wiki_client, commons_client)
      mwclient_page/mwclient_wraper.py   # MwClientPage class (edit, move, redirect check with retry)
      pages_api.py       # Thin wrappers: is_page_exists, is_redirect, edit_page, move_page
      category.py        # Category member listing
    sqlalchemy_db/       # SQLAlchemy models & services
    jobs_workers/        # Background job workers (BaseJobWorker pattern)
      base_worker.py     # Abstract base with lifecycle, retry, cancellation
      workers_list.py    # Job registry (jobs_data, jobs_data_public)
      create_owid_pages/ # Create OWID gallery pages from templates
      rename_owid_pages/ # Capitalize OWID subpage first letter (move/redirect)
      crop_main_files/   # Crop newest world files
    utils/               # Helper utilities
  templates/             # Jinja2 templates
    jobs_templates/admin/  # Job-specific detail/list templates
  app.py                 # WSGI entry point
tests/                   # Test files (mirror src structure)
_works_files/            # Offline CLI tools (not part of Flask app)
  rename_owid_pages.py   # Standalone OWID rename script (uses .env credentials)
```

## Background Jobs

### Adding a New Job

1. Create `src/main_app/jobs_workers/<job_name>/worker.py` with a class extending `BaseJobWorker`
2. Implement: `get_job_type()`, `get_initial_result()`, `process()`
3. Create `__init__.py` exporting the entry-point function
4. Register in `workers_list.py`: add to `jobs_data` (or `jobs_data_public` for public jobs)
5. Add sidebar item in `app_routes/admin/sidebar.py`
6. Create templates: `src/templates/jobs_templates/admin/<job_name>/list.html` and `details.html`

### MwClientPage Pattern

All mwclient operations go through `MwClientPage` which provides:
- `load_page()` — load page object, cache it
- `check_exists()` — check page existence
- `is_redirect()` — check if page is redirect using `page.redirects_to()`
- `edit_page(text, summary)` — edit with rate-limit retry
- `move_page(new_title, reason, ...)` — move/rename with rate-limit retry

Rate-limit retry: on `ratelimited` error, retries after 5s, 15s, 30s delays.

## Testing

-   Use pytest with fixtures defined in `conftest.py`
-   Mock external services (mwclient, network calls)
-   Use `pytest-mock` for mocking
-   Use `pytest-cov` for coverage
-   Mark network-dependent tests with `@pytest.mark.network`

## Environment Variables

Key variables (see CLAUDE.md for full list):

-   `FLASK_SECRET_KEY` - Required for sessions
-   `OAUTH_ENCRYPTION_KEY` - Required for OAuth
-   `OAUTH_CONSUMER_KEY/SECRET` - MediaWiki OAuth credentials
-   `TOOL_TOOLSDB_DBNAME/TOOL_TOOLSDB_HOST` - Database configuration
-   `MAIN_DIR` - Data storage path

## Important Notes

-   Never commit secrets or .env files
-   Always run tests before committing changes
-   Maintain test coverage for new code
