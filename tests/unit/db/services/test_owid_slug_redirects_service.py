from __future__ import annotations

import pytest

from src.main_app.db.services.owid_slug_redirects_service import OwidSlugRedirectsService


class TestOwidSlugRedirectsService:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service = OwidSlugRedirectsService()
        self.slug_redirect_record = self.service.create(slug="old-slug", redirect_to="new-slug")

    def test_add_new_slug_redirect_new(self) -> None:
        result = self.service.add_new_slug_redirect("old-slug1", "new-slug")

        assert result is not None
        assert result.slug == "old-slug1"
        assert result.redirect_to == "new-slug"

        # self.slug_redirect_record + result = 2
        assert self.service.count_slug_redirects() == 2

    def test_add_new_slug_redirect_existing(self) -> None:
        result = self.service.add_new_slug_redirect(
            self.slug_redirect_record.slug, self.slug_redirect_record.redirect_to
        )

        assert result is None
        assert self.service.count_slug_redirects() == 1

    def test_add_new_slug_redirect_update_target(self) -> None:
        result = self.service.update_slug_redirect(self.slug_redirect_record.id, {"redirect_to": "new-target"})

        assert result is not None
        assert result.redirect_to == "new-target"
        persisted = self.service.get(self.slug_redirect_record.id)
        assert persisted is not None
        assert persisted.redirect_to == "new-target"

    def test_list_slug_redirects(self) -> None:
        results = self.service.list_slug_redirects(limit=10, offset=0)

        assert len(results) == 1
        assert results[0].id == self.slug_redirect_record.id

    def test_get_slug_redirect_by_id(self) -> None:
        result = self.service.get_slug_redirect_by_id(self.slug_redirect_record.id)

        assert result is not None
        assert result.id == self.slug_redirect_record.id

    def test_update_slug_redirect(self) -> None:
        result = self.service.update_slug_redirect(self.slug_redirect_record.id, {"should_be_replaced": True})

        assert result is not None
        assert result.should_be_replaced is True
        persisted = self.service.get(self.slug_redirect_record.id)
        assert persisted is not None
        assert persisted.should_be_replaced is True

    def test_update_slug_redirect_returns_none_for_missing_record(self) -> None:
        assert self.service.update_slug_redirect(999, {"should_be_replaced": True}) is None

    def test_delete_slug_redirect(self) -> None:
        result = self.service.delete(self.slug_redirect_record.id)

        assert result is True
        assert self.service.get(self.slug_redirect_record.id) is None

    def test_count_slug_redirects(self) -> None:
        assert self.service.count_slug_redirects() == 1
