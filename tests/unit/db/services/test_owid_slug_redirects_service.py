from __future__ import annotations

import pytest

from src.main_app.db.models.owid_slug_redirects import OwidSlugRedirectRecord
from src.main_app.db.services.owid_slug_redirects_service import OwidSlugRedirectsService
from src.main_app.extensions import db


@pytest.fixture
def slug_redirect_record() -> OwidSlugRedirectRecord:
    record = OwidSlugRedirectRecord(slug="old-slug", redirect_to="new-slug")
    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record


class TestOwidSlugRedirectsService:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service = OwidSlugRedirectsService()

    def test_add_new_slug_redirect_new(self) -> None:
        result = self.service.add_new_slug_redirect("old-slug", "new-slug")

        assert result is not None
        assert result.slug == "old-slug"
        assert result.redirect_to == "new-slug"
        assert self.service.count_slug_redirects() == 1

    def test_add_new_slug_redirect_existing(self, slug_redirect_record: OwidSlugRedirectRecord) -> None:
        result = self.service.add_new_slug_redirect(slug_redirect_record.slug, slug_redirect_record.redirect_to)

        assert result is None
        assert self.service.count_slug_redirects() == 1

    def test_add_new_slug_redirect_update_target(self, slug_redirect_record: OwidSlugRedirectRecord) -> None:
        result = self.service.update_slug_redirect(slug_redirect_record.id, {"redirect_to": "new-target"})

        assert result is not None
        assert result.redirect_to == "new-target"
        persisted = self.service.get(slug_redirect_record.id)
        assert persisted is not None
        assert persisted.redirect_to == "new-target"

    def test_list_slug_redirects(self, slug_redirect_record: OwidSlugRedirectRecord) -> None:
        results = self.service.list_slug_redirects(limit=10, offset=0)

        assert len(results) == 1
        assert results[0].id == slug_redirect_record.id

    def test_get_slug_redirect_by_id(self, slug_redirect_record: OwidSlugRedirectRecord) -> None:
        result = self.service.get_slug_redirect_by_id(slug_redirect_record.id)

        assert result is not None
        assert result.id == slug_redirect_record.id

    def test_update_slug_redirect(self, slug_redirect_record: OwidSlugRedirectRecord) -> None:
        result = self.service.update_slug_redirect(slug_redirect_record.id, {"should_be_replaced": True})

        assert result is not None
        assert result.should_be_replaced is True
        persisted = self.service.get(slug_redirect_record.id)
        assert persisted is not None
        assert persisted.should_be_replaced is True

    def test_update_slug_redirect_returns_none_for_missing_record(self) -> None:
        assert self.service.update_slug_redirect(999, {"should_be_replaced": True}) is None

    def test_delete_slug_redirect(self, slug_redirect_record: OwidSlugRedirectRecord) -> None:
        result = self.service.delete(slug_redirect_record.id)

        assert result is True
        assert self.service.get(slug_redirect_record.id) is None

    def test_count_slug_redirects(self, slug_redirect_record: OwidSlugRedirectRecord) -> None:
        assert self.service.count_slug_redirects() == 1
