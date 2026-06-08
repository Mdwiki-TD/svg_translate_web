from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.main_app.db.models.owid_slug_redirects import OwidSlugRedirectRecord
from src.main_app.db.services.owid_slug_redirects_service import (
    add_new_slug_redirect,
    count_slug_redirects,
    delete_slug_redirect,
    get_slug_redirect_by_id,
    list_slug_redirects,
    update_slug_redirect,
)


@pytest.fixture
def mock_db_session(monkeypatch: pytest.MonkeyPatch):
    mock_session = MagicMock()
    monkeypatch.setattr("src.main_app.extensions.db.session", mock_session)
    return mock_session


def test_add_new_slug_redirect_new(mock_db_session):
    mock_db_session.query().filter().first.return_value = None

    add_new_slug_redirect("old-slug", "new-slug")

    assert mock_db_session.add.called
    assert mock_db_session.commit.called


def test_add_new_slug_redirect_existing(mock_db_session):
    mock_db_session.query().filter().first.return_value = OwidSlugRedirectRecord(
        slug="old-slug", redirect_to="new-slug"
    )

    add_new_slug_redirect("old-slug", "new-slug")

    assert not mock_db_session.add.called
    assert not mock_db_session.commit.called


def test_add_new_slug_redirect_update_target(mock_db_session):
    _existing = OwidSlugRedirectRecord(slug="old-slugz", redirect_to="old-target")
    mock_db_session.query().filter().first.return_value = _existing

    update_slug_redirect(_existing.id, {"redirect_to": "new-target"})
    existing_record = get_slug_redirect_by_id(_existing.id)
    assert existing_record.redirect_to == "new-target"
    assert mock_db_session.commit.called


def test_list_slug_redirects(mock_db_session):
    mock_db_session.query().order_by().limit().offset().all.return_value = []

    results = list_slug_redirects(limit=10, offset=0)

    assert results == []


def test_get_slug_redirect_by_id(mock_db_session):
    record = OwidSlugRedirectRecord(id=1)
    mock_db_session.query().filter().first.return_value = record

    result = get_slug_redirect_by_id(1)

    assert result == record


def test_update_slug_redirect(mock_db_session):
    record = OwidSlugRedirectRecord(id=1, should_be_replaced=False)
    mock_db_session.query().filter().first.return_value = record

    update_slug_redirect(1, {"should_be_replaced": True})

    assert record.should_be_replaced is True
    assert mock_db_session.commit.called


def test_delete_slug_redirect(mock_db_session):
    record = OwidSlugRedirectRecord(id=1)
    mock_db_session.query().filter().first.return_value = record

    result = delete_slug_redirect(1)

    assert result is True
    assert mock_db_session.delete.called
    assert mock_db_session.commit.called


def test_count_slug_redirects(mock_db_session):
    mock_db_session.query().count.return_value = 5

    assert count_slug_redirects() == 5
