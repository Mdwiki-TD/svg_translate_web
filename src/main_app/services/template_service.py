"""Utilities for managing administrator (template) accounts."""

from __future__ import annotations

import logging
from typing import List

from ..utils.wikitext.titles_utils import match_last_world_year

from ..config import settings
from ..db import has_db_config
from ..db.db_Templates import TemplateRecord, TemplatesDB

logger = logging.getLogger(__name__)

_TEMPLATE_STORE: TemplatesDB | None = None


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


def list_templates() -> List[TemplateRecord]:
    """Return all templates while keeping settings.admins in sync."""

    store = get_templates_db()

    coords = store.list()
    return coords


def ensure_last_world_year(template_data):
    if template_data.get("last_world_file") and not template_data.get("last_world_year"):
        template_data["last_world_year"] = match_last_world_year(template_data["last_world_file"])
    return template_data


def add_template_data(
    data: dict,
) -> TemplateRecord:
    """Add a template."""

    data = ensure_last_world_year(data)

    store = get_templates_db()
    record = store.add_data(data)

    return record


def update_template(
    template_id: int,
    title: str,
    main_file: str,
    last_world_file: str | None = None,
    source: str | None = None,
) -> TemplateRecord:
    """Update template."""

    store = get_templates_db()
    record = store.update(template_id, title, main_file, last_world_file, source)

    return record


def update_template_if_not_none(
    template_id: int,
    title: str | None = None,
    main_file: str | None = None,
    last_world_file: str | None = None,
    source: str | None = None,
) -> TemplateRecord:
    """Update template only if not None."""

    store = get_templates_db()
    record = store.update_if_not_none(template_id, title, main_file, last_world_file, source)

    return record


def update_template_data(
    template_id: int,
    template_data: dict[str, str],
) -> TemplateRecord:
    """Update template only if not None."""

    template_data = ensure_last_world_year(template_data)

    store = get_templates_db()
    record = store.update_template_data(template_id, template_data)

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
    "TemplateRecord",
    "TemplatesDB",
    "list_templates",
    "update_template",
    "delete_template",
    "get_template",
]
