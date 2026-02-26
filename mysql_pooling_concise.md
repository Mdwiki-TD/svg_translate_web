# MySQL Connection Pooling — Practical Fix Plan

**Problem:** MySQL error 1203 (`max_user_connections` exceeded)  
**Root cause:** No connection pooling — every operation opens a new raw PyMySQL connection  
**Solution:** Two small SQLAlchemy engines (one for web, one for background jobs)

---

## Why Two Engines?

| | Web Engine | Background Engine |
|--|-----------|-------------------|
| Users | Gunicorn workers | Job workers |
| Pool size | 3 | 4 |
| Max overflow | 1 | 0 |
| Peak connections | 7 × 2 pods × 4 = **56** | 4 × 2 pods × 4 = **32** |
| **Total** | | **88 / 100** ✅ |

---

## Step 1 — Add dependency

```txt
# requirements.txt
sqlalchemy>=2.0.0
```

---

## Step 2 — Create `src/main_app/db/engine_factory.py`

```python
"""Shared SQLAlchemy engines with connection pooling."""

import threading
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.pool import QueuePool

from ..config import DbConfig, settings

_http_engine       = None
_bg_engine         = None
_http_lock         = threading.Lock()   # prevent race condition on first init
_bg_lock           = threading.Lock()


def _make_url(cfg: DbConfig) -> URL:
    # URL.create() handles special characters in passwords automatically
    return URL.create(
        drivername="mysql+pymysql",
        username=cfg.db_user,
        password=cfg.db_password,
        host=cfg.db_host,
        database=cfg.db_name,
        query={"charset": "utf8mb4"},
    )


def get_http_engine():
    """Web engine — small pool shared across Gunicorn workers."""
    global _http_engine
    if _http_engine is not None:
        return _http_engine
    with _http_lock:
        if _http_engine is None:
            _http_engine = create_engine(
                _make_url(settings.database_data),
                poolclass=QueuePool,
                pool_size=3,
                max_overflow=1,
                pool_recycle=3600,
                pool_pre_ping=True,  # discard stale connections silently
                pool_timeout=30,
                echo=False,
            )
    return _http_engine


def get_bg_engine():
    """Background engine — isolated pool so batch jobs never starve HTTP requests."""
    global _bg_engine
    if _bg_engine is not None:
        return _bg_engine
    with _bg_lock:
        if _bg_engine is None:
            _bg_engine = create_engine(
                _make_url(settings.database_data),
                poolclass=QueuePool,
                pool_size=4,
                max_overflow=0,      # fixed pool — no overflow for batch work
                pool_recycle=3600,
                pool_pre_ping=True,
                pool_timeout=60,     # batch jobs can wait longer
                echo=False,
            )
    return _bg_engine


@contextmanager
def db_connection(engine=None, readonly=False):
    """
    Borrow a connection from the pool, commit or rollback on exit.

    Args:
        engine:   Defaults to the web engine.
        readonly: Skip commit() for SELECT-only calls.
    """
    eng  = engine or get_http_engine()
    conn = eng.connect()
    try:
        yield conn
        if not readonly:
            conn.commit()
    except Exception:
        if not readonly:
            conn.rollback()
        raise
    finally:
        conn.close()   # returns connection to pool


def dispose_all():
    """Release all pool connections — call on app shutdown."""
    if _http_engine:
        _http_engine.dispose()
    if _bg_engine:
        _bg_engine.dispose()
```

---

## Step 3 — Update `db_class.py` (minimal change)

Replace the raw `connect()` call with a pool-borrowed connection:

```python
# Before — opens a new connection every time
self.connection = pymysql.connect(...)

# After — borrow from pool via context manager
from .engine_factory import db_connection

with db_connection() as conn:
    result = conn.execute(text("SELECT ..."), params)
```

If the existing class is used as a context manager throughout the codebase, add a thin wrapper instead of rewriting every call site:

```python
class Database:
    def __init__(self, db_config: DbConfig):
        from .engine_factory import get_http_engine
        self._engine = get_http_engine()

    def execute(self, sql: str, params=None):
        with db_connection(self._engine) as conn:
            return conn.execute(text(sql), params or {})

    def fetch(self, sql: str, params=None) -> list[dict]:
        with db_connection(self._engine, readonly=True) as conn:
            result = conn.execute(text(sql), params or {})
            return [dict(r._mapping) for r in result]
```

---

## Step 4 — Update background workers

Each worker in `jobs_workers/` should use `get_bg_engine()` instead of creating its own connection:

```python
# Before — each worker opens a fresh connection
self.db = Database(database_data)   # raw PyMySQL connection

# After — borrow from the isolated background pool
from ..db.engine_factory import get_bg_engine, db_connection

class SomeWorker:
    def run(self):
        with db_connection(engine=get_bg_engine()) as conn:
            conn.execute(text("UPDATE tasks SET ..."), {...})
```

---

## Step 5 — Register shutdown hook

```python
# In src/main_app/__init__.py  (create_app)
import atexit
from .db.engine_factory import dispose_all

atexit.register(dispose_all)
```

---

## Checklist

- [ ] Add `sqlalchemy>=2.0.0` to `requirements.txt`
- [ ] Create `engine_factory.py` (Step 2)
- [ ] Update `db_class.py` to use `db_connection()` (Step 3)
- [ ] Update each file in `jobs_workers/` to use `get_bg_engine()` (Step 4)
- [ ] Register `dispose_all` on shutdown (Step 5)
- [ ] Deploy and verify with `SHOW STATUS LIKE 'Threads_connected'`

---

## Quick Verification

```sql
-- Run on MySQL during load test — should stay under 90
SHOW STATUS LIKE 'Threads_connected';

-- Check per-user connection count
SELECT user, count(*) 
FROM information_schema.processlist 
GROUP BY user;
```
