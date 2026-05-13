"""
engine.py
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import Text, create_engine, event, inspect, text
from sqlalchemy.dialects.mysql import LONGTEXT as LONGTEXTSQLALCHEMY
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.types import TypeDecorator

logger = logging.getLogger(__name__)


class LONGTEXT(TypeDecorator):
    """LONGTEXT for MySQL, Text for everything else."""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "mysql":
            return dialect.type_descriptor(LONGTEXTSQLALCHEMY())
        return dialect.type_descriptor(Text())


# ---------------------------------------------------------------------------
# 1. Model — replaces coordinator_model.py + CREATE TABLE
# ---------------------------------------------------------------------------


class BaseDb(DeclarativeBase):
    """
    Base class for database models.
    Provides common functionality like to_dict.
    """

    def to_dict(self) -> dict[str, Any]:
        """Convert ORM object to dictionary."""
        data = {column.name: getattr(self, column.name) for column in self.__table__.columns}

        if "add_date" in data and self.add_date:
            data["add_date"] = self.add_date.isoformat() if hasattr(self.add_date, "isoformat") else str(self.add_date)

        if "date" in data and self.date:
            data["date"] = self.date.isoformat() if hasattr(self.date, "isoformat") else str(self.date)

        for column in self.__table__.columns:
            if column.nullable is False and data[column.name] is None:
                data[column.name] = column.default

        return data


# ---------------------------------------------------------------------------
# 2. Database connection — replaces db_driver.py entirely
#    pool_pre_ping=True handles reconnect + retry automatically
# ---------------------------------------------------------------------------


def build_db_url(db_data: dict[str, str]) -> str:
    """

    db_name: str
    db_host: str
    db_user: str | None
    db_password: str | None
    """
    db_user = db_data["db_user"]
    db_password = db_data["db_password"]
    db_host = db_data["db_host"]
    db_name = db_data["db_name"]
    return f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"


def build_engine(db_url: str) -> Engine:
    """
    Create a SQLAlchemy engine.
    """
    kwargs = {
        "pool_pre_ping": True,  # replaces _ensure_connection and retry logic
    }

    if not db_url.startswith("sqlite"):
        kwargs.update(
            {
                "pool_size": 5,
                "max_overflow": 10,
                "pool_recycle": 3600,  # recycle connections after 1 hour
                "connect_args": {
                    "connect_timeout": 5,
                    "init_command": 'SET time_zone = "+00:00"',
                    "charset": "utf8mb4",
                    # "collation": "utf8mb4_unicode_ci",
                },
            }
        )
    return create_engine(db_url, **kwargs)


# ---------------------------------------------------------------------------
# 3. SessionFactory singleton — replaces _COORDINATORS_STORE
# ---------------------------------------------------------------------------


_SessionFactory: sessionmaker | None = None


def init_db(db_url: str, create_tables: bool = False) -> None:
    """
    Initialize the engine and SessionFactory.
    Call once at application startup.

    create_tables=True: creates the table if it does not exist (useful for testing).
    """
    global _SessionFactory
    engine = build_engine(db_url)
    if create_tables:
        real_tables = [t for t in BaseDb.metadata.tables.values() if not t.info.get("is_view")]

        BaseDb.metadata.create_all(engine, tables=real_tables)
    _SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)


def get_session() -> Session:
    """Return a new session. Always use inside a `with` block."""
    if _SessionFactory is None:
        # For migration purposes, if not initialized, we might need a way to initialize it
        # But according to instructions, we should just use it.
        # In a real app, init_db would be called at startup.
        raise RuntimeError("Call init_db() before using the database.")
    return _SessionFactory()


# -----------------------------------------------------------------------------
# Create views automatically when tables are created
# -----------------------------------------------------------------------------


@event.listens_for(BaseDb.metadata, "after_create")
def create_views_new_all_view(target, connection, **kw):
    inspector = inspect(connection)
    existing_views = inspector.get_view_names()

    views_to_create = {
        table.name: table.info.get("create_query")
        for table in target.tables.values()
        if table.info.get("is_view") and table.info.get("create_query")
    }

    for name, query in views_to_create.items():
        if name not in existing_views:
            try:
                connection.execute(text(query))
                logger.info(f"Successfully created view: {name}")
            except Exception as e:
                logger.exception(f"Error creating view {name}", exc_info=True)
        else:
            logger.info(f"View '{name}' already exists, skipping.")


__all__ = [
    # Model
    "BaseDb",
    # Setup
    "init_db",
    "get_session",
    "LONGTEXT",
]
