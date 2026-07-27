from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.main_app.db.models.owid_slug_redirects import OwidSlugRedirectRecord
from src.main_app.db.services.owid_slug_redirects_service import OwidSlugRedirectsService


@pytest.fixture
def mock_db_session(monkeypatch: pytest.MonkeyPatch):
    mock_session = MagicMock()
    monkeypatch.setattr("src.main_app.extensions.db.session", mock_session)
    return mock_session


class TestOwidSlugRedirectsService:
    @pytest.fixture(autouse=True)
    def setup(self, mock_db_session):
        self.service = OwidSlugRedirectsService()

    def test_add_new_slug_redirect_new(self, mock_db_session):
        mock_db_session.query().filter().first.return_value = None

        self.service.add_new_slug_redirect("old-slug", "new-slug")

        # assert mock_db_session.add.called
        assert mock_db_session.commit.called

    def test_add_new_slug_redirect_existing(self, mock_db_session):
        mock_db_session.query().filter().first.return_value = OwidSlugRedirectRecord(
            slug="old-slug", redirect_to="new-slug"
        )

        self.service.add_new_slug_redirect("old-slug", "new-slug")

        # assert not mock_db_session.add.called
        assert not mock_db_session.commit.called

    def test_add_new_slug_redirect_update_target(self, mock_db_session):
        _existing = OwidSlugRedirectRecord(id=100, slug="old-slugz", redirect_to="old-target")
        mock_db_session.get.return_value = _existing

        self.service.update_slug_redirect(100, {"redirect_to": "new-target"})
        assert _existing.redirect_to == "new-target"
        assert mock_db_session.commit.called

    def test_list_slug_redirects(self, mock_db_session):
        mock_db_session.execute().scalars().all.return_value = []

        results = self.service.list_slug_redirects(limit=10, offset=0)

        assert results == []

    def test_get_slug_redirect_by_id(self, mock_db_session):
        record = OwidSlugRedirectRecord(id=1)
        mock_db_session.get.return_value = record

        result = self.service.get_slug_redirect_by_id(1)

        assert result == record

    def test_update_slug_redirect(self, mock_db_session):
        record = OwidSlugRedirectRecord(id=1, should_be_replaced=False)
        mock_db_session.get.return_value = record

        self.service.update_slug_redirect(1, {"should_be_replaced": True})

        assert record.should_be_replaced is True
        assert mock_db_session.commit.called

    def test_delete_slug_redirect(self, mock_db_session):
        record = OwidSlugRedirectRecord(id=1)
        mock_db_session.query().filter().first.return_value = record

        result = self.service.delete(1)

        assert result is True
        assert mock_db_session.delete.called
        assert mock_db_session.commit.called

    def test_count_slug_redirects(self, mock_db_session):
        mock_db_session.query().count.return_value = 5

        assert self.service.count_slug_redirects() == 5
