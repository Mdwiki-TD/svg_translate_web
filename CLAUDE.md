# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SVG Translate Web is a Flask-based web application for copying SVG translations between different language versions on Wikimedia Commons. It runs on Wikimedia Toolforge and uses MediaWiki OAuth for authentication.

## Development Commands

### Installation

```bash
pip install -r src/requirements.txt
pip install -r requirements-test.txt  # For testing
```

### Running the Application

```bash
python -m flask --app src.app run
python src/app.py debug  # Debug mode
```

### Testing

```bash
pytest                           # Run all tests
pytest tests/test_file.py        # Run specific test file
pytest --cov=src                 # Run with coverage
pytest -m skip2                  # Run tests marked with skip2
```

### Code Formatting

```bash
black .                          # Format with Black (line length: 120)
isort .                          # Sort imports
```

## Architecture

### Flask Application Factory

The app uses the factory pattern via `create_app()` in `src/app/__init__.py`. Routes are organized as Flask blueprints under `src/app/app_routes/`.

### Task Pipeline (8 stages)

Translation tasks run through a sequential pipeline defined in `src/app/threads/web_run_task.py`:

1. **initialize** - Starting workflow
2. **text** - Fetch wiki text from template
3. **titles** - Extract file titles from text
4. **translations** - Load translations from main SVG
5. **download** - Download SVG files from Commons
6. **nested** - Analyze nested file structures
7. **inject** - Inject translations into SVGs
8. **upload** - Upload results to Wikimedia Commons

Tasks run in background threads with cancellation support via `threading.Event`. Progress is tracked in MySQL tables (`tasks` and `task_stages`).

### Database Layer

-   `TaskStorePyMysql` (composed via mixins: `CreateUpdateTask`, `StageStore`, `TasksListDB`) handles task persistence
-   `UserTokenRecord` manages encrypted OAuth token storage
-   Connection wrapper in `src/app/db/db_class.py` provides retry logic

### Key Route Blueprints

| Blueprint       | Prefix            | Location                 |
| --------------- | ----------------- | ------------------------ |
| `bp_main`       | `/`               | `app_routes/main/`       |
| `bp_auth`       | `/auth`           | `app_routes/auth/`       |
| `bp_tasks`      | `/task`, `/tasks` | `app_routes/tasks/`      |
| `bp_explorer`   | `/explorer`       | `app_routes/explorer/`   |
| `bp_admin`      | `/admin`          | `app_routes/admin/`      |
| `bp_templates`  | `/templates`      | `app_routes/templates/`  |
| `bp_fix_nested` | `/fix-nested`     | `app_routes/fix_nested/` |
| `bp_extract`    | `/extract`        | `app_routes/extract/`    |

### Configuration

-   Environment variables loaded via `src/svg_config.py` using python-dotenv
-   Dataclasses define typed config: `Settings`, `DbConfig`, `OAuthConfig`, `PathsConfig`
-   Settings cached via `@lru_cache` in `src/app/config.py`
-   Required env vars: `FLASK_SECRET_KEY`, `OAUTH_ENCRYPTION_KEY`, `OAUTH_CONSUMER_KEY`, `OAUTH_CONSUMER_SECRET`, `DB_*`, `MAIN_DIR`

### External Dependencies

-   **CopySVGTranslation**: Core SVG translation library (external package)
-   **mwclient/mwoauth**: MediaWiki API and OAuth integration
-   **lxml**: XML/SVG processing
-   **Fernet encryption**: OAuth token encryption

## Deployment

Automated via GitHub Actions on `main` branch push to Wikimedia Toolforge Kubernetes. See `service.template` for resource configuration (2 replicas, 3 CPU, 6GB memory).
