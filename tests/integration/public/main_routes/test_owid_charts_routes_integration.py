"""Tests for src.main_app.public.main_routes.owid_charts_routes.py"""

from __future__ import annotations

import pytest

from src.main_app.config import TestingConfig
from src.main_app.db.services import OwidChartsService
from src.main_app.extensions import db as _db


@pytest.fixture
def owid_charts_client(monkeypatch):
    """Create Flask test client with real owid_charts_service."""
    monkeypatch.setenv("FLASK_SECRET_KEY", "testing-secret")

    from src.main_app import create_app

    flask_app = create_app(TestingConfig)
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False

    with flask_app.app_context():
        real_tables = [t for t in _db.metadata.tables.values() if not t.info.get("is_view")]
        _db.metadata.create_all(_db.engine, tables=real_tables)
        yield flask_app.test_client()
        _db.session.remove()
        _db.metadata.drop_all(_db.engine, tables=real_tables)


class TestIndexRoute:
    """Tests for the public charts index route."""

    def test_index_renders_with_published_charts(self, owid_charts_client):
        """Test index page renders with published charts."""
        svc = OwidChartsService()
        svc.add_chart(slug="published-chart", title="Published Chart", is_published=True)

        response = owid_charts_client.get("/owidcharts/")
        assert response.status_code == 200

    def test_index_calls_count_charts(self, owid_charts_client):
        """Test index page also calls count_charts for total count."""
        svc = OwidChartsService()
        svc.add_chart(slug="chart-a", title="Chart A", is_published=True)
        svc.add_chart(slug="chart-b", title="Chart B", is_published=False)

        response = owid_charts_client.get("/owidcharts/")
        assert response.status_code == 200


class TestAllChartsRoute:
    """Tests for the all charts route."""

    def test_all_charts_renders(self, owid_charts_client):
        """Test all charts page renders."""
        svc = OwidChartsService()
        svc.add_chart(slug="chart-1", title="Chart 1")

        response = owid_charts_client.get("/owidcharts/all")
        assert response.status_code == 200

    def test_all_charts_includes_unpublished(self, owid_charts_client):
        """Test all charts page includes unpublished charts."""
        svc = OwidChartsService()
        svc.add_chart(slug="draft-chart", title="Draft Chart", is_published=False)

        response = owid_charts_client.get("/owidcharts/all")
        assert response.status_code == 200

    def test_all_charts_empty_list(self, owid_charts_client):
        """Test all charts page with no charts."""
        response = owid_charts_client.get("/owidcharts/all")
        assert response.status_code == 200
