"""Utilities for managing administrator (coordinator) accounts."""

from __future__ import annotations

import logging
from typing import List

from ..db_CoordinatorsDB import CoordinatorsDB
from ..models import AdminUserRecord
from .check_db import get_main_db, initialize_db

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
        # Convert a database row dictionary to an AdminUserRecord object
    """
    global _ADMINS_STORE

    if _ADMINS_STORE is None:
        _ADMINS_STORE = initialize_db(CoordinatorsDB, get_main_db())

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
