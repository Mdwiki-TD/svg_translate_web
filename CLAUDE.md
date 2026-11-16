# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SVG Translate Web is a Flask-based web application for copying SVG translations between different language versions on Wikimedia Commons. It runs on Wikimedia Toolforge and uses MediaWiki OAuth for authentication.

## Development Commands

### Installation

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For testing
```

### Running the Application

```bash
# Development server
python -m flask --app www.python.src.app run

# Debug mode
python www/python/src/app.py debug
```

The application will be available at `http://localhost:5000`

### Testing

```bash
pytest                           # Run all tests (excludes network and todo markers)
pytest tests/test_file.py       # Run specific test file
pytest tests/test_file.py::test_func  # Run single test function
pytest --cov=www/python/src     # Run with coverage
pytest -m "not network"         # Skip network tests
pytest -m "not network and not todo"  # Skip network and todo tests
```

Test markers:
- `unit`: unit tests
- `integration`: integration tests
- `network`: tests requiring network access
- `todo`: tests not yet implemented

### Code Formatting

```bash
black .                         # Format with Black (line length: 120)
isort .                         # Sort imports (profile: black)
ruff check --fix src/          # Lint with auto-fix
```

### Linting

Configuration in `pyproject.toml`:

```bash
ruff check src/                # Lint with Ruff
mypy www/python/src/           # Type checking with mypy
pyright www/python/src/        # Type checking with Pyright
pylint --rcfile=pyproject.toml www/python/src/  # Additional linting
```

All tools use line length 120 and target Python 3.13.

## Architecture

### Project Structure

```
www/python/src/
├── app.py                      # WSGI entry point
├── main_app/
│   ├── __init__.py            # Flask app factory (AppFactory.create())
│   ├── config.py              # Settings dataclasses with @lru_cache
│   ├── admin/                 # Admin panel (sidebar, routes, auth)
│   │   └── routes/           # Admin sub-routes (coordinators, jobs, etc.)
│   ├── public/               # Flask blueprints
│   │   ├── auth/             # OAuth authentication
│   │   ├── main/             # Main routes (bp_main at /)
│   │   ├── tasks/            # Task management (bp_tasks at /tasks)
│   │   ├── explorer/         # File explorer (bp_explorer at /explorer)
│   │   ├── templates/        # Template management (bp_templates at /templates)
│   │   ├── fix_nested/       # Nested SVG fixes (bp_fix_nested at /fix-nested)
│   │   └── extract/          # Extract routes (bp_extract at /extract)
│   ├── api_services/         # MediaWiki API clients
│   │   ├── clients/          # mwclient site builders
│   │   ├── mwclient_page/mwclient_wraper.py  # MwClientPage class
│   │   └── pages_api.py      # Thin wrappers: is_page_exists, edit_page, move_page
│   ├── sqlalchemy_db/        # SQLAlchemy models & services
│   ├── database/             # Database layer (TaskStorePyMysql, UserTokenRecord)
│   ├── jobs_workers/         # Background job workers
│   │   ├── base_worker.py    # Abstract BaseJobWorker with lifecycle, retry, cancellation
│   │   ├── workers_list.py   # Job registry (jobs_data_admins, jobs_data_public)
│   │   ├── copy_svg_langs/   # Main translation task pipeline
│   │   ├── create_owid_pages/
│   │   ├── rename_owid_pages/
│   │   └── crop_main_files/
│   └── utils/                # Helper utilities
├── templates/                # Jinja2 templates
│   └── jobs_templates/admin/ # Job-specific detail/list templates
└── static/                   # CSS, JS, favicon

tests/                        # Test files (mirror src structure)
_works_files/                 # Offline CLI tools (not part of Flask app)
```

### Flask Application Factory

The app uses the factory pattern via `AppFactory.create()` in `www/python/src/main_app/__init__.py`. Routes are organized as Flask blueprints under `www/python/src/main_app/public/`.

### Task Pipeline (8 stages)

Translation tasks run through a sequential pipeline defined in `www/python/src/main_app/jobs_workers/copy_svg_langs/job.py`:

1. **text** - Fetch wiki text from template
2. **titles** - Extract file titles from text
3. **translations** - Load translations from main SVG
4. **download** - Download SVG files from Commons
5. **nested** - Analyze nested file structures
6. **inject** - Inject translations into SVGs
7. **upload** - Upload results to Wikimedia Commons

### Database Layer

- Uses Flask-SQLAlchemy for database operations
- Database URI configured via `DATABASE_URI` environment variable
- Models and services located in `www/python/src/main_app/sqlalchemy_db/`
- Connection pooling configured in `www/python/src/main_app/config/flask_config.py`

### Key Route Blueprints

| Blueprint       | Prefix        | Location                          |
| --------------- | ------------- | --------------------------------- |
| `bp_main`       | `/`           | `public/main/`                    |
| `bp_auth`       | `/auth`       | `public/auth/`                    |
| `bp_tasks`      | `/tasks`      | `public/tasks/`                   |
| `bp_explorer`   | `/explorer`   | `public/explorer/`                |
| `bp_admin`      | `/admin`      | `public/admin/`                   |
| `bp_templates`  | `/templates`  | `public/templates/`               |
| `bp_fix_nested` | `/fix-nested` | `public/fix_nested/`              |
| `bp_extract`    | `/extract`    | `public/extract/`                 |

### Configuration

- Environment variables loaded via `www/python/src/main_app/config/classes.py` using python-dotenv (expects `.env` file in `www/python/src/`)
- Dataclasses define typed config: `Settings`, `SecurityConfig`, `OAuthConfig`, `Paths`, `CookieConfig`, `JobsConfig`, `OtherConfig`, `SessionConfig`
- Settings cached via `@lru_cache` in `get_settings()` function
- Flask-SQLAlchemy configuration in `www/python/src/main_app/config/flask_config.py`

#### Required Environment Variables

```bash
# Flask
FLASK_SECRET_KEY=           # Generate: python -c "import secrets; print(secrets.token_hex(16))"

# Database (SQLAlchemy)
DATABASE_URI=               # e.g., mysql+pymysql://user:pass@host/dbname or sqlite:///instance.db

# OAuth
OAUTH_MWURI=https://commons.wikimedia.org/w/index.php
OAUTH_CONSUMER_KEY=
OAUTH_CONSUMER_SECRET=
OAUTH_ENCRYPTION_KEY=       # Generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Storage
MAIN_DIR=/path/to/data      # Root for svg_data/, logs/, etc.

# Security
AUTH_COOKIE_NAME=uid_enc_copy
AUTH_COOKIE_MAX_AGE=2592000  # 30 days
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Other
WIKI_DOMAIN=commons.wikimedia.org
USER_AGENT="Copy SVG Translations/1.0 (https://copy-svg-langs.toolforge.org; your-email@example.org)"
```

### Background Jobs (Admin)

Background jobs are registered in `www/python/src/main_app/jobs_workers/workers_list.py` and use `BaseJobWorker` (`www/python/src/main_app/jobs_workers/base_worker.py`) for lifecycle management.

| Job Type                    | Worker Location                                 | Purpose                                       |
| --------------------------- | ----------------------------------------------- | --------------------------------------------- |
| `collect_templates_data`    | `jobs_workers/collect_templates_data_worker.py` | Collect template metadata from Commons        |
| `crop_main_files`           | `jobs_workers/crop_main_files/`                 | Crop newest world files                       |
| `create_owid_pages`         | `jobs_workers/create_owid_pages/`               | Create OWID gallery pages from templates      |
| `rename_owid_pages`         | `jobs_workers/rename_owid_pages/`               | Capitalize first letter of OWID subpage names |
| `add_svglanguages_template` | `jobs_workers/add_svglanguages_template/`       | Add {{SVGLanguages}} template to files        |
| `fix_nested_main_files`     | `jobs_workers/fix_nested_main_files_worker.py`  | Fix nested SVG file structures                |
| `download_main_files`       | `jobs_workers/download_main_files_worker.py`    | Download main files from Commons              |

#### Adding a New Job

1. Create `www/python/src/main_app/jobs_workers/<job_name>/worker.py` with a class extending `BaseJobWorker`
2. Implement: `get_job_type()`, `get_initial_result()`, `process()`
3. Create `__init__.py` exporting the entry-point function
4. Register in `workers_list.py`: add to `jobs_data_admins` (or `jobs_data_public` for public jobs)
5. Add sidebar item in `public/admin/sidebar.py`
6. Create templates: `www/python/src/templates/jobs_templates/admin/<job_name>/list.html` and `details.html`

Jobs use the current user's OAuth session (via `get_user_site(user)`) for wiki operations.

### MediaWiki Page Operations

All wiki page operations go through `MwClientPage` (`www/python/src/main_app/api_services/mwclient_page/mwclient_wraper.py`) which handles:

- Page loading, existence checks, redirect detection (uses `page.redirects_to()`)
- Editing with rate-limit retry (5s, 15s, 30s delays)
- Moving (renaming) with rate-limit retry

Thin wrappers in `pages_api.py`:

```python
is_page_exists(title, site)  # Check if page exists
is_redirect(title, site)     # Check if page is a redirect
edit_page(site, title, text, summary)  # Edit page content
move_page(site, title, new_title, reason, ...)  # Move/rename page
```

### Offline Tools (`_works_files/`)

Standalone CLI scripts not part of the Flask app:

- **`rename_owid_pages.py`** — Capitalize OWID subpage names using WIKI_USERNAME/WIKI_PASSWORD from `.env`. Dry-run by default; use `--apply` to execute.

### External Dependencies

- **CopySVGTranslation**: Core SVG translation library (external package)
- **mwclient/mwoauth**: MediaWiki API and OAuth integration
- **lxml**: XML/SVG processing
- **cryptography.Fernet**: OAuth token encryption
- **flask-limiter**: Rate limiting

## Code Style Guidelines

### Python Style

- **Line length**: 120 characters (configured in pyproject.toml)
- **Target version**: Python 3.13 (minimum 3.11)
- **Formatter**: Black
- **Import sorter**: isort (profile: black, multi_line_output: 3)

### Imports

Use `from __future__ import annotations` at the top of all Python files. Import order:

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

- **Classes**: `PascalCase` (e.g., `TaskStorePyMysql`, `DbConfig`)
- **Functions/Methods**: `snake_case` (e.g., `get_settings`, `format_task`)
- **Variables**: `snake_case` (e.g., `task_id`, `file_name`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `TASK_STORE`, `MAX_RETRIES`)
- **Private**: prefix with `_` (e.g., `_load_db_data`, `_cleanup_connections`)

### Type Hints

Use type hints throughout. Use `|` for union types (Python 3.11+):

```python
def get_page_text(file_name: str, site: mwclient.Site | None) -> str: ...
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

- Use specific exceptions and log with `logger.exception()` for stack traces
- Return meaningful error dictionaries: `{"success": False, "error": "message"}`
- Use validation helpers like `verify_required_fields()`
- Handle exceptions gracefully, never expose sensitive info

### Flask Patterns

- Use Blueprints for route organization
- Use application factory pattern (`AppFactory.create()`)
- Register error handlers for 400, 403, 404, 405, 500, CSRFError
- Use `@lru_cache` for expensive configuration loading

### Logging

- Use module-level loggers: `logger = logging.getLogger(__name__)`
- Use f-strings for dynamic content
- Use appropriate levels: debug, info, warning, error, exception

## Deployment

### Toolforge Deployment

Automated via GitHub Actions on `main` branch push to Wikimedia Toolforge Kubernetes.

Configuration in `service.template`:

```yaml
backend: kubernetes
cpu: 3
mem: 6Gi
replicas: 2
type: python3.13
```

#### Filesystem Layout on Toolforge

```
$HOME/
├── www/python/
│   ├── venv/                    # Virtualenv
│   └── src/                     # Application source (TARGET_DIR)
│       ├── app.py               # WSGI entry point
│       ├── uwsgi.ini            # uWSGI configuration
│       ├── main_app/            # Application package
│       ├── templates/           # Jinja2 templates
│       ├── static/              # CSS, JS, favicon
│       └── requirements.txt
├── data/                        # Runtime data (MAIN_DIR default)
│   ├── svg_data/                # Downloaded SVG files
│   ├── svg_data_thumb/          # SVG thumbnails
│   ├── logs/                    # Application logs (daily rotation in prod)
│   ├── svg_jobs/                # Job working directories
│   ├── main_files/              # Main file storage
│   ├── fix_nested_data/         # Nested SVG fix data
│   └── crop_main_files/         # Cropped file cache
├── toolforge/
│   └── deploy_scripts/          # Shell scripts
└── service.template
```

### Manual Deployment

1. Ensure all environment variables are configured on Toolforge
2. Upload the code to Toolforge
3. Install dependencies: `pip install -r requirements.txt`
4. Start the webservice: `toolforge-webservice python3.13 start`

## Testing

- Use pytest with fixtures defined in `conftest.py`
- Mock external services (mwclient, network calls)
- Use `pytest-mock` for mocking
- Use `pytest-cov` for coverage
- Mark network-dependent tests with `@pytest.mark.network`
- Tests are organized in `tests/unit/`, `tests/integration/`, and `tests/network/`

## Important Notes

- Never commit secrets or .env files
- Always run tests before committing changes
- Maintain test coverage for new code
- The `.env` file should be in `www/python/src/`, not the root directory
- Copy from `src/example.env` to `src/.env` for initial setup
