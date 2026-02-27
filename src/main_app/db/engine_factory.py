"""Shared SQLAlchemy engines with connection pooling."""

import threading
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.pool import QueuePool

from ..config import DbConfig, settings

_http_engine = None
_bg_engine = None
_http_lock = threading.Lock()  # prevent race condition on first init
_bg_lock = threading.Lock()


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
                max_overflow=0,  # fixed pool — no overflow for batch work
                pool_recycle=3600,
                pool_pre_ping=True,
                pool_timeout=60,  # batch jobs can wait longer
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
    eng = engine or get_http_engine()
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
        conn.close()  # returns connection to pool


def dispose_all():
    """Release all pool connections — call on app shutdown."""
    global _http_engine, _bg_engine
    if _http_engine:
        _http_engine.dispose()
        _http_engine = None
    if _bg_engine:
        _bg_engine.dispose()
        _bg_engine = None
