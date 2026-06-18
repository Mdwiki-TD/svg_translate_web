from __future__ import annotations

from datetime import datetime

from sqlalchemy import Index, UniqueConstraint

from src.main_app.db.models.owid_slug_redirects import OwidSlugRedirectRecord


def test_owid_slug_redirect_record_initialization() -> None:
    """Test OwidSlugRedirectRecord initialization with required fields."""
    rec = OwidSlugRedirectRecord(id=1, slug="test-slug", redirect_to="test-redirect", should_be_replaced=False)

    assert rec.id == 1
    assert rec.slug == "test-slug"
    assert rec.redirect_to == "test-redirect"
    assert rec.should_be_replaced is False


def test_owid_slug_redirect_record_with_all_fields() -> None:
    """Test OwidSlugRedirectRecord initialization with all fields."""
    dt = datetime(2025, 6, 1, 10, 30, 0)
    rec = OwidSlugRedirectRecord(
        id=10,
        slug="health-expenditure",
        redirect_to="health-expenditure-v2",
        should_be_replaced=True,
        created_at=dt,
    )

    assert rec.id == 10
    assert rec.slug == "health-expenditure"
    assert rec.redirect_to == "health-expenditure-v2"
    assert rec.should_be_replaced is True
    assert rec.created_at == dt


def test_owid_slug_redirect_record_to_dict() -> None:
    """Test to_dict returns all expected keys with correct values."""
    dt = datetime(2025, 6, 1, 10, 30, 0)
    rec = OwidSlugRedirectRecord(
        id=5,
        slug="old-slug",
        redirect_to="new-slug",
        should_be_replaced=True,
        created_at=dt,
    )

    result = rec.to_dict()

    assert result["id"] == 5
    assert result["slug"] == "old-slug"
    assert result["redirect_to"] == "new-slug"
    assert result["should_be_replaced"] is True
    assert result["created_at"] == "2025-06-01T10:30:00"


def test_owid_slug_redirect_record_to_dict_datetime_isoformat() -> None:
    """Test to_dict converts datetime to ISO format string."""
    dt = datetime(2024, 12, 25, 8, 15, 30)
    rec = OwidSlugRedirectRecord(id=1, slug="s", redirect_to="r", created_at=dt)

    result = rec.to_dict()

    assert result["created_at"] == "2024-12-25T08:15:30"


def test_owid_slug_redirect_record_ignores_unknown_kwargs() -> None:
    """Test __init__ silently ignores unknown keyword arguments."""
    rec = OwidSlugRedirectRecord(id=1, slug="test", redirect_to="dest", unknown_field="ignored")

    assert rec.id == 1
    assert rec.slug == "test"
    assert rec.redirect_to == "dest"
    assert not hasattr(rec, "unknown_field")


def test_owid_slug_redirect_record_table_name() -> None:
    """Test that OwidSlugRedirectRecord points to the 'owid_slug_redirects' table."""
    assert OwidSlugRedirectRecord.__tablename__ == "owid_slug_redirects"


def test_owid_slug_redirect_record_table_args() -> None:
    """Test that OwidSlugRedirectRecord has the expected constraints and indexes."""
    assert len(OwidSlugRedirectRecord.__table_args__) == 3

    unique_constraint = OwidSlugRedirectRecord.__table_args__[0]
    assert isinstance(unique_constraint, UniqueConstraint)
    assert unique_constraint.name == "unique_slug_redirect"
    assert tuple(c.key for c in unique_constraint.columns) == ("slug", "redirect_to")

    slug_index = OwidSlugRedirectRecord.__table_args__[1]
    assert isinstance(slug_index, Index)
    assert slug_index.name == "idx_slug"
    assert tuple(c.key for c in slug_index.columns) == ("slug",)

    redirect_index = OwidSlugRedirectRecord.__table_args__[2]
    assert isinstance(redirect_index, Index)
    assert redirect_index.name == "idx_redirect_to"
    assert tuple(c.key for c in redirect_index.columns) == ("redirect_to",)
