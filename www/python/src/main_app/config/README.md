# config — Configuration Subsystem

## Project Overview

Configuration subsystem using **frozen dataclasses** loaded from environment variables. Supports Development, Production, and Testing configurations with a singleton `settings` instance.

### Files

| File               | Purpose                                                    |
| ------------------ | ---------------------------------------------------------- |
| `__init__.py`      | Re-exports all config classes and the `settings` singleton |
| `classes.py`       | Frozen dataclass definitions for all config sections       |
| `main_settings.py` | Environment variable loading + `@lru_cache` singleton      |
| `flask_config.py`  | Flask-specific config classes + SQLAlchemy URI builder     |

### Configuration Classes

```
Settings (root)
├── paths: Paths                    # Log, jobs, public_jobs directories
├── cookie: CookieConfig            # Session cookie settings
├── sessions: SessionConfig         # Flask session keys
├── oauth: OAuthConfig              # MediaWiki OAuth credentials
├── security: SecurityConfig        # Secret key, form limits, key rotation
├── jobs: JobsConfig                # Background job worker settings
└── other: OtherConfig              # CSRF, user-agent, wiki domain
```

### Flask Config Hierarchy

```
Config (base)
├── DevelopmentConfig  # DEBUG=True, TESTING=True
├── ProductionConfig   # Strict security settings
└── TestingConfig      # CSRF disabled, SQLite in-memory
```

## Architecture & Code Quality Review

### Design

- All config objects are `@dataclass(frozen=True)` — **immutable after creation**
- `Settings` is the root container with nested config objects
- `get_settings()` is `@lru_cache(maxsize=1)` — singleton pattern
- Environment variables are read at module import time
- Validation: `FLASK_SECRET_KEY` and OAuth config are required (raise `RuntimeError`)
- `TestingConfig` uses SQLite in-memory and disables CSRF

### Environment Variables

| Variable                | Required | Default      | Description                     |
| ----------------------- | -------- | ------------ | ------------------------------- |
| `FLASK_SECRET_KEY`      | Yes      | —            | Flask secret key                |
| `OAUTH_MWURI`           | Yes      | —            | MediaWiki OAuth URI             |
| `OAUTH_CONSUMER_KEY`    | Yes      | —            | OAuth consumer key              |
| `OAUTH_CONSUMER_SECRET` | Yes      | —            | OAuth consumer secret           |
| `OAUTH_ENCRYPTION_KEY`  | Yes      | —            | Fernet key for token encryption |
| `DATABASE_URI`          | Yes      | ``           | SQLAlchemy database URI         |
| `MAIN_DIR`              | No       | `~/data`     | Base directory for logs/jobs    |
| `WIKI_DOMAIN`           | No       | `mdwiki.org` | Target wiki domain              |
| `WTF_CSRF_TIME_LIMIT`   | No       | `3600`       | CSRF token lifetime (seconds)   |

## Testing

```bash
pytest tests/unit/config --cov=src/main_app/config
```

## Strengths

- **Frozen dataclasses** prevent accidental config mutation
- **Clean separation** of Flask config vs application config
- **SQLAlchemy URI builder** with proper URL encoding (`quote_plus`)
- **Connection pool settings** with `pool_pre_ping`, `pool_recycle`, `pool_size`
- **Secret key rotation** support via `SECRET_KEY_FALLBACKS`
- **Form security limits** — `MAX_CONTENT_LENGTH`, `MAX_FORM_MEMORY_SIZE`, `MAX_FORM_PARTS`

## Weaknesses

- **Config loaded at import time** — hard to test with different env vars
- **`@lru_cache`** makes it impossible to reload config without restart
- **`DbConfig.to_dict()`** exposes password in plain dict form
- **No config validation** beyond required fields (e.g., no port range checks)
- **`DevelopmentConfig`** has `SESSION_COOKIE_SECURE=True` — requires HTTPS even locally
- **No `.env.example`** documenting all variables

## Critical Issues

> **Warning**: `DevelopmentConfig` forces secure cookies, making local HTTP development difficult.

## Areas That Need Attention

- [ ] Add `.env.example` with all variables documented
- [ ] Set `SESSION_COOKIE_SECURE=False` in `DevelopmentConfig`
- [ ] Add validation for numeric ranges (e.g., pool_size > 0)
- [ ] Remove or encrypt `DbConfig.to_dict()` password field

## Improvement Plan

### Quick Wins

1. Fix `DevelopmentConfig.SESSION_COOKIE_SECURE` to `False`
2. Create `.env.example`

### Medium-Term

1. Add config validation with descriptive error messages
2. Support config file (TOML/YAML) as alternative to env vars

### Long-Term

1. Use `pydantic-settings` for validated config with env var support

## Comprehensive Review

| Metric                   | Score                                          |
| ------------------------ | ---------------------------------------------- |
| **Overall Rating**       | **7/10**                                       |
| **Production Readiness** | Good — immutable config with proper validation |
| **Technical Debt**       | Low                                            |
| **Risk Assessment**      | Low                                            |
| **Maintainability**      | 7/10                                           |
