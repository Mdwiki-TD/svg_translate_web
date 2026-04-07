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
-   Dataclasses define typed config: `Settings`, `DbConfig`, `OAuthConfig`, `Paths`, `CookieConfig`, `DownloadConfig`, `SecurityConfig`
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
ADMINS=user1,user2          # Comma-separated admin usernames
DISABLE_UPLOADS=0           # Set to 1 to disable uploads
DEV_DOWNLOAD_LIMIT=10       # Limit downloads in dev (0 = unlimited)
```

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
