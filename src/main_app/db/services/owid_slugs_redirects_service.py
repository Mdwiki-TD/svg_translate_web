from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import desc

from ...extensions import db
from ..models.owid_slug_redirects import OwidSlugRedirectRecord
from .utils import db_guard_rollback

logger = logging.getLogger(__name__)


@db_guard_rollback
def add_new_slug_redirect(slug: str, redirect_to: str) -> None:
    """
    Add a new slug redirect record if it doesn't already exist.
    """
    existing = (
        db.session.query(OwidSlugRedirectRecord)
        .filter(OwidSlugRedirectRecord.slug == slug, OwidSlugRedirectRecord.redirect_to == redirect_to)
        .first()
    )

    if not existing:
        new_record = OwidSlugRedirectRecord(slug=slug, redirect_to=redirect_to)
        db.session.add(new_record)
        db.session.commit()
        logger.info(f"Added new slug redirect: {slug} -> {redirect_to}")


def list_slug_redirects(limit: int | None = None, offset: int | None = None) -> list[OwidSlugRedirectRecord]:
    """
    List slug redirects ordered by created_at DESC.
    """
    query = db.session.query(OwidSlugRedirectRecord).order_by(desc(OwidSlugRedirectRecord.created_at))
    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
    return query.all()


def get_slug_redirect_by_id(redirect_id: int) -> OwidSlugRedirectRecord | None:
    """
    Fetch a slug redirect by ID.
    """
    return db.session.query(OwidSlugRedirectRecord).filter(OwidSlugRedirectRecord.id == redirect_id).first()


@db_guard_rollback
def update_slug_redirect(redirect_id: int, data: dict[str, Any]) -> OwidSlugRedirectRecord | None:
    """
    Update a slug redirect record.
    """
    record = get_slug_redirect_by_id(redirect_id)
    if record:
        for key, value in data.items():
            if hasattr(OwidSlugRedirectRecord, key):
                setattr(record, key, value)
        db.session.commit()
        db.session.refresh(record)
    return record


@db_guard_rollback
def delete_slug_redirect(redirect_id: int) -> bool:
    """
    Delete a slug redirect record.
    """
    record = get_slug_redirect_by_id(redirect_id)
    if record:
        db.session.delete(record)
        db.session.commit()
        return True
    return False


def count_slug_redirects() -> int:
    """
    Count total slug redirect records.
    """
    return db.session.query(OwidSlugRedirectRecord).count()


__all__ = [
    "add_new_slug_redirect",
    "list_slug_redirects",
    "get_slug_redirect_by_id",
    "update_slug_redirect",
    "delete_slug_redirect",
    "count_slug_redirects",
]
