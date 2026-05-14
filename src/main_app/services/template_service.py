"""Utilities for managing TemplatesDB"""

from __future__ import annotations

import logging
from typing import Any, List

from ..config import settings
from ..db.db_Templates import TemplatesDB
from ..db.exceptions import InsufficientDatabaseConfigError
from ..db.models import TemplateRecord
from ..utils.wikitext.titles_utils import match_last_world_year

logger = logging.getLogger(__name__)

_TEMPLATE_STORE: TemplatesDB | None = None


def _ensure_last_world_year(template_data):
    if template_data.get("last_world_file") and not template_data.get("last_world_year"):
        template_data["last_world_year"] = match_last_world_year(template_data["last_world_file"])

    if template_data.get("slug") and "/grapher/" in template_data["slug"]:
        template_data["slug"] = template_data["slug"].split("/grapher/", maxsplit=1)[1].split("?")[0]

    return template_data


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
        if not settings.has_db_config():
            raise InsufficientDatabaseConfigError()

        try:
            _TEMPLATE_STORE = TemplatesDB(settings.database_data)
        except Exception as exc:  # pragma: no cover - defensive guard for startup failures
            logger.exception("Failed to initialize MySQL template store")
            raise RuntimeError("Unable to initialize template store") from exc

    return _TEMPLATE_STORE


def list_templates(limit: int | None = None) -> List[TemplateRecord]:
    """Return all templates"""
    store = get_templates_db()
    coords = store.list()
    return coords


def get_template(template_id: int) -> TemplateRecord:
    """Fetch a template by ID."""
    store = get_templates_db()
    return store.fetch_by_id(template_id)


def get_template_by_title(title: str) -> TemplateRecord:
    """Fetch a template by title."""
    store = get_templates_db()
    return store.fetch_by_title(title)


def add_template_data(
    data: dict[str, Any],
) -> TemplateRecord:
    """
    Add a new template.
    """
    data = _ensure_last_world_year(data)

    store = get_templates_db()
    record = store.add_data(data)

    return record


def update_template_data(
    template_id: int,
    template_data: dict[str, str],
) -> TemplateRecord:
    """
    Update template only if not None.
    """
    template_data = _ensure_last_world_year(template_data)

    store = get_templates_db()
    record = store.update_template_data(template_id, template_data)

    return record


def delete_template(template_id: int) -> bool:
    """Delete a template."""

    store = get_templates_db()
    return store.delete(template_id)


__all__ = [
    "get_template_by_title",
    "add_template_data",
    "update_template_data",
    "list_templates",
    "delete_template",
    "get_template",
    "get_templates_db",
]
