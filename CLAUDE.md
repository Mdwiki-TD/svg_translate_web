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
python -m flask --app src.app run
python src/app.py debug  # Debug mode
```

### Testing

```bash
pytest                           # Run all tests
pytest tests/test_file.py       # Run specific test file
pytest -k test_function_name    # Run specific test function
pytest --cov=src                # Run with coverage
pytest -m "not network"         # Skip network tests
```

### Code Formatting

```bash
black .                         # Format with Black (line length: 120)
isort .                         # Sort imports
```

### Linting

Configuration files are in `0/` directory:

```bash
flake8 --config=0/.flake8 src    # Linting (max line: 100)
pylint --rcfile=0/.pylintrc src  # Additional linting
mypy --config-file=0/mypy.ini src # Type checking
```

## Architecture

### Flask Application Factory

The app uses the factory pattern via `create_app()` in `src/main_app/__init__.py`. Routes are organized as Flask blueprints under `src/main_app/app_routes/`.

### Task Pipeline (8 stages)

Translation tasks run through a sequential pipeline defined in `src/main_app/jobs_workers/copy_svg_langs/job.py`:

2. **text** - Fetch wiki text from template
3. **titles** - Extract file titles from text
4. **translations** - Load translations from main SVG
5. **download** - Download SVG files from Commons
6. **nested** - Analyze nested file structures
7. **inject** - Inject translations into SVGs
8. **upload** - Upload results to Wikimedia Commons


### Database Layer

-   `TaskStorePyMysql` (composed via mixins: `CreateUpdateTask`, `StageStore`, `TasksListDB`) handles task persistence
-   `UserTokenRecord` manages encrypted OAuth token storage
-   Connection wrapper in `src/main_app/db/db_class.py` provides retry logic

### Key Route Blueprints

| Blueprint       | Prefix        | Location                 |
| --------------- | ------------- | ------------------------ |
| `bp_main`       | `/`           | `app_routes/main/`       |
| `bp_auth`       | `/auth`       | `app_routes/auth/`       |
| `bp_tasks`      | `/tasks`      | `app_routes/tasks/`      |
| `bp_explorer`   | `/explorer`   | `app_routes/explorer/`   |
| `bp_admin`      | `/admin`      | `app_routes/admin/`      |
| `bp_templates`  | `/templates`  | `app_routes/templates/`  |
| `bp_fix_nested` | `/fix-nested` | `app_routes/fix_nested/` |
| `bp_extract`    | `/extract`    | `app_routes/extract/`    |

### Configuration

-   Environment variables loaded via `src/svg_config.py` using python-dotenv (expects `.env` file in `src/`)
-   Dataclasses define typed config: `Settings`, `DbConfig`, `OAuthConfig`, `Paths`, `CookieConfig`, `JobsConfig`, `SecurityConfig`
-   Settings cached via `@lru_cache` in `src/main_app/config.py`

#### Required Environment Variables

```bash
# Flask
FLASK_SECRET_KEY=           # Generate: python -c "import secrets; print(secrets.token_hex(16))"

# Database
DB_NAME=svg_langs
DB_HOST=127.0.0.1
TOOL_REPLICA_USER=
TOOL_REPLICA_PASSWORD=

# OAuth
OAUTH_MWURI=https://commons.wikimedia.org/w/index.php
OAUTH_CONSUMER_KEY=
OAUTH_CONSUMER_SECRET=
OAUTH_ENCRYPTION_KEY=       # Generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Storage
MAIN_DIR=/path/to/data      # Root for svg_data/, logs/, etc.

# Optional
DISABLE_UPLOADS=0           # Set to 1 to disable uploads
DEV_DOWNLOAD_LIMIT=10       # Limit downloads in dev (0 = unlimited)
```

### Background Jobs (Admin)

Background jobs are registered in `src/main_app/jobs_workers/workers_list.py` and use `BaseJobWorker` (`src/main_app/jobs_workers/base_worker.py`) for lifecycle management.

| Job Type                    | Worker Location                                         | Purpose                                                  |
| --------------------------- | ------------------------------------------------------- | -------------------------------------------------------- |
| `collect_main_files`        | `jobs_workers/collect_main_files_worker.py`             | Collect template metadata from Commons                   |
| `crop_main_files`           | `jobs_workers/crop_main_files/`                         | Crop newest world files                                  |
| `create_owid_pages`         | `jobs_workers/create_owid_pages/`                       | Create OWID gallery pages from templates                 |
| `rename_owid_pages`         | `jobs_workers/rename_owid_pages/`                       | Capitalize first letter of OWID subpage names            |
| `add_svglanguages_template` | `jobs_workers/add_svglanguages_template/`               | Add {{SVGLanguages}} template to files                   |
| `fix_nested_main_files`     | `jobs_workers/fix_nested_main_files_worker.py`          | Fix nested SVG file structures                           |
| `download_main_files`       | `jobs_workers/download_main_files_worker.py`            | Download main files from Commons                         |

Jobs use the current user's OAuth session (via `get_user_site(user)`) for wiki operations.

### MediaWiki Page Operations (`api_services/pages_api.py`)

All wiki page operations go through `MwClientPage` (`api_services/mwclient_page.py`) which handles:
- Page loading, existence checks, redirect detection
- Editing with rate-limit retry (5s, 15s, 30s delays)
- Moving (renaming) with rate-limit retry

Thin wrappers in `pages_api.py`:

```python
is_page_exists(title, site)   # Check if page exists
is_redirect(title, site)      # Check if page is a redirect (uses page.redirects_to())
edit_page(site, title, text, summary)  # Edit page content
move_page(site, title, new_title, reason, ...)  # Move/rename page
```

### Offline Tools (`_works_files/`)

Standalone CLI scripts not part of the Flask app:

- **`rename_owid_pages.py`** — Capitalize OWID subpage names using WIKI_USERNAME/WIKI_PASSWORD from `.env`. Dry-run by default; use `--apply` to execute.

### External Dependencies

-   **CopySVGTranslation**: Core SVG translation library (external package)
-   **mwclient/mwoauth**: MediaWiki API and OAuth integration
-   **lxml**: XML/SVG processing
-   **cryptography.Fernet**: OAuth token encryption

## Deployment

Automated via GitHub Actions on `main` branch push to Wikimedia Toolforge Kubernetes. See `service.template` for resource configuration (2 replicas, 3 CPU, 6GB memory).

## File Locations

-   Source code: `src/`
-   Tests: `tests/`
-   Templates: `src/templates/`
-   Static assets: `src/static/`
-   Config files: `0/` (flake8, pylint, mypy)
-   Deployment scripts: `web_sh/`
