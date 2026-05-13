"""Utilities for managing TemplatesNeedUpdateDB"""

from __future__ import annotations

import logging
from typing import List

from ..config import settings
from ..db import has_db_config
from ..db.db_Templates import TemplatesDB
from ..db.db_TemplatesNeedUpdate import TemplatesNeedUpdateDB
from ..shared.models import TemplateNeedUpdateRecord

logger = logging.getLogger(__name__)

_TEMPLATE_UPDATE_STORE: TemplatesDB | None = None


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


def list_templates_need_update() -> List[TemplateNeedUpdateRecord]:
    """Return all templates"""
    store = get_templates_need_update_db()
    coords = store.list()
    return coords


__all__ = [
    "get_templates_need_update_db",
    "list_templates_need_update",
]
