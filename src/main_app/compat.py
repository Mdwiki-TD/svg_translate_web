"""
Backward-compatible session bridge for the SQLAlchemy → Flask-SQLAlchemy migration.

During the migration period, services can import `get_session` from here.
- Inside a Flask request/app context: returns the Flask-SQLAlchemy `db.session`
- Outside Flask context (CLI scripts, workers): falls back to the legacy sessionmaker

Once all services are migrated to use `db.session` directly, this module can be removed.
"""

from __future__ import annotations

from flask import has_app_context

from .extensions import db


def get_session():
    """Return the appropriate SQLAlchemy session.

    If running inside a Flask application context (request, CLI command, test),
    returns the Flask-SQLAlchemy scoped session which is automatically cleaned up.

    Otherwise, falls back to the legacy get_session() from engine.py for
    standalone scripts or workers that don't push an app context.
    """
    if has_app_context():
        return db.session

    # Fallback for code running outside Flask context
    from .sqlalchemy_db.engine import get_session as legacy_get_session

    return legacy_get_session()
