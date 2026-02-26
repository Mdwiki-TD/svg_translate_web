"""Utilities for managing administrator (template) accounts."""

from __future__ import annotations

import logging
from typing import List

from .config import settings
from .db import has_db_config
from .db.db_Templates import TemplateRecord, TemplatesDB

logger = logging.getLogger(__name__)

_TEMPLATE_STORE: TemplatesDB | None = None
_TEMPLATE_STORE_BG: TemplatesDB | None = None


def get_templates_db() -> TemplatesDB:
    """
    Return the module's cached TemplatesDB instance, initializing it on first use.

    Returns:
        TemplatesDB: The initialized and cached templates database instance.

    Raises:
        RuntimeError: If no database configuration is available.
        RuntimeError: If initializing the TemplatesDB fails.
    """
    global _TEMPLATE_STORE

    if _TEMPLATE_STORE is None:
        if not has_db_config():
            raise RuntimeError(
                "Template administration requires database configuration; no fallback store is available."
            )

        try:
            _TEMPLATE_STORE = TemplatesDB(settings.database_data)
        except Exception as exc:  # pragma: no cover - defensive guard for startup failures
            logger.exception("Failed to initialize MySQL template store")
            raise RuntimeError("Unable to initialize template store") from exc

    return _TEMPLATE_STORE


def get_templates_db_bg() -> TemplatesDB:
    """
    Return the module's cached TemplatesDB instance for background workers.

    Uses the background engine pool to avoid starving HTTP requests.

    Returns:
        TemplatesDB: The initialized and cached templates database instance.

    Raises:
        RuntimeError: If no database configuration is available.
        RuntimeError: If initializing the TemplatesDB fails.
    """
    global _TEMPLATE_STORE_BG

    if _TEMPLATE_STORE_BG is None:
        if not has_db_config():
            raise RuntimeError(
                "Template administration requires database configuration; no fallback store is available."
            )

        try:
            _TEMPLATE_STORE_BG = TemplatesDB(settings.database_data, use_bg_engine=True)
        except Exception as exc:  # pragma: no cover - defensive guard for startup failures
            logger.exception("Failed to initialize MySQL template store for background workers")
            raise RuntimeError("Unable to initialize template store for background workers") from exc

    return _TEMPLATE_STORE_BG


def list_templates() -> List[TemplateRecord]:
    """Return all templates while keeping settings.admins in sync."""

    store = get_templates_db()

    coords = store.list()
    return coords


def add_template(title: str, main_file: str, last_world_file: str | None = None) -> TemplateRecord:
    """Add a template."""

    store = get_templates_db()
    record = store.add(title, main_file, last_world_file)

    return record


def update_template(template_id: int, title: str, main_file: str, last_world_file: str | None = None) -> TemplateRecord:
    """Update template."""

    store = get_templates_db()
    record = store.update(template_id, title, main_file, last_world_file)

    return record


def update_template_if_not_none(
    template_id: int,
    title: str | None = None,
    main_file: str | None = None,
    last_world_file: str | None = None,
) -> TemplateRecord:
    """Update template only if not None."""

    store = get_templates_db()
    record = store.update_if_not_none(template_id, title, main_file, last_world_file)

    return record


def delete_template(template_id: int) -> TemplateRecord:
    """Delete a template."""

    store = get_templates_db()
    record = store.delete(template_id)

    return record


def get_template(template_id: int) -> TemplateRecord:
    """Fetch a single template by ID."""
    store = get_templates_db()
    return store.fetch_by_id(template_id)


__all__ = [
    "get_templates_db",
    "get_templates_db_bg",
    "TemplateRecord",
    "TemplatesDB",
    "list_templates",
    "add_template",
    "update_template",
    "delete_template",
    "get_template",
]
