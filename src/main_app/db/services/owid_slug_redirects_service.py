from __future__ import annotations

import logging
from typing import Any

from ...extensions import db
from ..models.owid_slug_redirects import OwidSlugRedirectRecord
from .crud_service import CRUDService

logger = logging.getLogger(__name__)


class OwidSlugRedirectsService(CRUDService[OwidSlugRedirectRecord]):
    def __init__(self) -> None:
        super().__init__(db.session, OwidSlugRedirectRecord)

    def list_slug_redirects(self, limit: int | None = None, offset: int | None = None) -> list[OwidSlugRedirectRecord]:
        return self.list(
            limit=limit,
            offset=offset,
            order_by=[OwidSlugRedirectRecord.created_at.desc()],
        )

    def get_slug_redirect_by_id(self, redirect_id: int) -> OwidSlugRedirectRecord | None:
        """
        Fetch a slug redirect by ID.
        """
        return self.get_record_by_id(redirect_id)

    def count_slug_redirects(self) -> int:
        return self.session.query(OwidSlugRedirectRecord).count()

    def add_new_slug_redirect(self, slug: str, redirect_to: str) -> None:
        """
        Add a new slug redirect record if it doesn't already exist.
        """
        existing = self.get_by(
            slug=slug,
            redirect_to=redirect_to,
        )
        if existing:
            logger.info("Slug redirect already exists: %s -> %s", slug, redirect_to)
            return None
        return self.create_safe(slug=slug, redirect_to=redirect_to)

    def update_slug_redirect(self, redirect_id: int, data: dict[str, Any]) -> OwidSlugRedirectRecord | None:
        """
        Update a slug redirect record.
        """
        record = self.get_slug_redirect_by_id(redirect_id)
        if not record:
            return None
        return self.update(record, **data)

    def bulk_update_slug_redirects(self, redirect_ids: list[int], data: dict[str, Any]) -> None:
        """
        Bulk update slug redirect records.
        """
        allowed_keys = {"should_be_replaced"}
        update_data = {k: v for k, v in data.items() if k in allowed_keys}
        if update_data and redirect_ids:
            try:
                self.session.query(OwidSlugRedirectRecord).filter(OwidSlugRedirectRecord.id.in_(redirect_ids)).update(
                    update_data, synchronize_session=False
                )
                self.session.commit()
            except Exception as e:
                self.session.rollback()
                return

    def bulk_delete_slug_redirects(self, redirect_ids: list[int]) -> None:
        """
        Bulk delete slug redirect records.
        """
        if not redirect_ids:
            return
        try:
            self.session.query(OwidSlugRedirectRecord).filter(OwidSlugRedirectRecord.id.in_(redirect_ids)).delete(
                synchronize_session=False
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            return


__all__ = [
    "OwidSlugRedirectsService",
]
