"""Utilities for managing administrator (coordinator) accounts."""

from __future__ import annotations

import logging
from typing import List

from ..db.exceptions import InsufficientDatabaseConfigError

from ..config import settings
from ..db.db_CoordinatorsDB import AdminUserRecord, CoordinatorsDB

logger = logging.getLogger(__name__)

_ADMINS_STORE: CoordinatorsDB | None = None


def get_admins_db() -> CoordinatorsDB:
    """
    Return the singleton coordinators database store, initializing it on first access.

    Initializes and caches a CoordinatorsDB using settings.database_data if no store exists.
    Raises a RuntimeError if database configuration is missing or if initialization fails.

    Returns:
        CoordinatorsDB: The cached coordinators database instance.

    Raises:
        RuntimeError: If database configuration is not available or the store cannot be initialized.
    """
    global _ADMINS_STORE

    if _ADMINS_STORE is None:
        if not settings.has_db_config():
            raise InsufficientDatabaseConfigError()

        try:
            _ADMINS_STORE = CoordinatorsDB(settings.database_data)
        except Exception as exc:  # pragma: no cover - defensive guard for startup failures
            logger.exception("Failed to initialize MySQL coordinator store")
            raise RuntimeError("Unable to initialize coordinator store") from exc

    return _ADMINS_STORE


def list_coordinators() -> List[AdminUserRecord]:
    """Return all coordinators."""

    store = get_admins_db()

    coords = store.list()
    return coords


def active_coordinators() -> list[str]:
    """Return usernames of all active coordinators."""

    store = get_admins_db()

    return [u.username for u in store.list() if u.is_active]


def get_coordinator_by_id(coordinator_id: int) -> AdminUserRecord:
    """
    Get a coordinator by ID.
    """
    store = get_admins_db()
    record = store.get_by_id(coordinator_id)
    return record


def add_coordinator(username: str) -> AdminUserRecord:
    """Add a coordinator."""

    if not username:
        raise ValueError("Username is required")

    store = get_admins_db()
    try:
        record = store.get_by_username(username)
    except LookupError:
        record = None
    if record:
        # This assumes a UNIQUE constraint on the username column
        raise ValueError(f"Coordinator '{username}' already exists") from None

    record = store.add(username)

    return record


def set_coordinator_active(coordinator_id: int, is_active: bool) -> AdminUserRecord:
    """Toggle coordinator activity."""
    store = get_admins_db()
    record = store.get_by_id(coordinator_id)
    if record:
        record = store.set_active(coordinator_id, is_active)
    return record


def delete_coordinator(coordinator_id: int) -> bool:
    """Delete a coordinator."""

    store = get_admins_db()
    return store.delete(coordinator_id)


__all__ = [
    "get_coordinator_by_id",
    "list_coordinators",
    "active_coordinators",
    "add_coordinator",
    "set_coordinator_active",
    "delete_coordinator",
]
