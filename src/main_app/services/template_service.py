"""Utilities for managing administrator (template) accounts."""

from __future__ import annotations

import logging
from typing import List

from ..config import settings
from ..db import has_db_config
from ..db.db_Templates import TemplatesDB
from ..db.db_TemplatesNeedUpdate import TemplatesNeedUpdateDB
from ..shared.models import TemplateNeedUpdateRecord, TemplateRecord
from ..utils.wikitext.titles_utils import match_last_world_year

logger = logging.getLogger(__name__)

_TEMPLATE_STORE: TemplatesDB | None = None
_TEMPLATE_UPDATE_STORE: TemplatesDB | None = None


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


def get_templates_need_update_db() -> TemplatesNeedUpdateDB:
    """
    Return the module's cached TemplatesNeedUpdateDB instance, initializing it on first use.

    Returns:
        TemplatesNeedUpdateDB: The initialized and cached templates database instance.

    Raises:
        RuntimeError: If no database configuration is available.
        RuntimeError: If initializing the TemplatesNeedUpdateDB fails.
    """
    global _TEMPLATE_UPDATE_STORE

    if _TEMPLATE_UPDATE_STORE is None:
        if not has_db_config():
            raise RuntimeError(
                "Template administration requires database configuration; no fallback store is available."
            )

        try:
            _TEMPLATE_UPDATE_STORE = TemplatesNeedUpdateDB(settings.database_data)
        except Exception as exc:  # pragma: no cover - defensive guard for startup failures
            logger.exception("Failed to initialize MySQL template store")
            raise RuntimeError("Unable to initialize template store") from exc

    return _TEMPLATE_UPDATE_STORE


def list_templates() -> List[TemplateRecord]:
    """Return all templates while keeping settings.admins in sync."""
    store = get_templates_db()
    coords = store.list()
    return coords


def list_templates_need_update() -> List[TemplateNeedUpdateRecord]:
    """Return all templates"""
    store = get_templates_need_update_db()
    coords = store.list()
    return coords


def slugify_title(title: str) -> str:
    """Derive a slug from a template title."""
    # Remove 'Template:OWID/' or 'Template:' prefix
    if title.startswith("Template:OWID/"):
        name = title[len("Template:OWID/") :]
    elif title.startswith("Template:"):
        name = title[len("Template:") :]
    else:
        name = title

    # Lowercase, replace spaces and underscores with hyphens
    slug = name.lower().replace(" ", "-").replace("_", "-")
    # Remove any other non-alphanumeric characters (except hyphens)
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    # Remove multiple hyphens
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def ensure_last_world_year(template_data):
    if template_data.get("last_world_file") and not template_data.get("last_world_year"):
        template_data["last_world_year"] = match_last_world_year(template_data["last_world_file"])

    # If slug is provided as a full URL, extract the slug part
    if template_data.get("slug") and "/grapher/" in template_data["slug"]:
        template_data["slug"] = template_data["slug"].split("/grapher/", maxsplit=1)[1].split("?")[0]

    # If slug is still empty but we have a source URL, try extracting from source
    if not template_data.get("slug") and template_data.get("source") and "/grapher/" in template_data["source"]:
        template_data["slug"] = template_data["source"].split("/grapher/", maxsplit=1)[1].split("?")[0]

    # If slug is still empty, derive it from the title
    if not template_data.get("slug") and template_data.get("title"):
        template_data["slug"] = slugify_title(template_data["title"])

    return template_data


def add_template_data(
    data: dict,
) -> TemplateRecord:
    """Add a template."""

    data = ensure_last_world_year(data)

    store = get_templates_db()
    record = store.add_data(data)

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
    "add_template_data",
    "update_template_data",
    "get_templates_db",
    "TemplateRecord",
    "TemplatesDB",
    "list_templates",
    "delete_template",
    "get_template",
    "list_templates_need_update",
]
