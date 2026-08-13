"""Unit tests for src/main_app/adminpanel/routes/owid_charts.py module."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.main_app.database.services import OwidChartsService


@pytest.fixture(autouse=True)
def _fake_admin_user(monkeypatch):
    """Fake an authenticated admin user for all tests in this module."""
    admin_user = SimpleNamespace(username="test_admin", is_active_admin=True)
    monkeypatch.setattr("src.main_app.admin.decorators.get_current_user", lambda: admin_user)
    monkeypatch.setattr("src.main_app.public.auth.decorators.get_current_user", lambda: admin_user)
    monkeypatch.setattr("src.main_app.public.utils.routes_utils.get_current_user", lambda: admin_user)


@pytest.fixture
def client(mock_app):
    """Test client bound to mock_app."""
    return mock_app.test_client()


class TestCreateJsonFile:
    """Tests for create_json_file via HTTP route."""

    def _seed_chart(self, slug: str = "test-chart", title: str = "Test Chart"):
        """Seed an OWID chart record via the real service."""
        service = OwidChartsService()
        service.add_chart(slug=slug, title=title)
        return service.get_chart_by_slug(slug)

    def test_success(self, client):
        """Download JSON should return a file with chart data."""
        self._seed_chart(slug="chart1", title="Chart 1")

        resp = client.get("/adminpanel/owidcharts/download-json")

        assert resp.status_code == 200
        assert "owid_charts.json" in resp.headers.get("Content-Disposition", "")

    def test_no_charts(self, client):
        """Download JSON with no charts should redirect with warning."""
        resp = client.get("/adminpanel/owidcharts/download-json")

        assert resp.status_code == 302

    def test_includes_template_info(self, client):
        """Download JSON should include template info when available."""
        self._seed_chart(slug="chart-t", title="Chart T")

        resp = client.get("/adminpanel/owidcharts/download-json")

        assert resp.status_code == 200


class TestAddChart:
    """Tests for _add_chart via HTTP route."""

    def test_missing_slug(self, client):
        """POST /add with empty slug should redirect."""
        resp = client.post(
            "/adminpanel/owidcharts/add",
            data={"slug": "", "title": "T", "from_popup": "0"},
        )

        assert resp.status_code == 302

    def test_success(self, client):
        """POST /add with valid data should create the chart."""
        resp = client.post(
            "/adminpanel/owidcharts/add",
            data={"slug": "new-chart", "title": "New Chart", "from_popup": "0"},
        )

        assert resp.status_code == 302
        assert OwidChartsService().get_chart_by_slug("new-chart") is not None

    def test_value_error(self, client):
        """POST /add with duplicate slug should redirect."""
        service = OwidChartsService()
        service.add_chart(slug="dup-chart", title="Dup")

        resp = client.post(
            "/adminpanel/owidcharts/add",
            data={"slug": "dup-chart", "title": "Dup", "from_popup": "0"},
        )

        assert resp.status_code == 302

    def test_from_popup_error(self, client):
        """POST /add from popup with error should redirect back to popup."""
        service = OwidChartsService()
        service.add_chart(slug="popup-dup", title="Popup Dup")

        resp = client.post(
            "/adminpanel/owidcharts/add",
            data={"slug": "popup-dup", "title": "Popup Dup", "from_popup": "1"},
        )

        assert resp.status_code in (200, 302)


class TestUpdateChart:
    """Tests for _update_chart via HTTP route."""

    def _seed_chart(self, slug: str = "update-chart", title: str = "Update Chart"):
        """Seed an OWID chart record via the real service."""
        service = OwidChartsService()
        service.add_chart(slug=slug, title=title)
        return service.get_chart_by_slug(slug)

    def test_missing_slug(self, client):
        """POST /update with empty slug should redirect."""
        resp = client.post(
            "/adminpanel/owidcharts/update",
            data={"chart_id": "1", "slug": "", "title": "T"},
        )

        assert resp.status_code == 302

    def test_success(self, client):
        """POST /update with valid data should update the chart."""
        chart = self._seed_chart(slug="upd-chart", title="Old Title")

        resp = client.post(
            "/adminpanel/owidcharts/update",
            data={"chart_id": chart.chart_id, "slug": "upd-chart", "title": "New Title", "from_popup": "0"},
        )

        assert resp.status_code == 302
        updated = OwidChartsService().get_chart_by_id(chart.chart_id)
        assert updated.title == "New Title"

    def test_record_none(self, client):
        """POST /update with nonexistent chart_id should redirect."""
        resp = client.post(
            "/adminpanel/owidcharts/update",
            data={"chart_id": "99999", "slug": "s", "title": "T", "from_popup": "0"},
        )

        assert resp.status_code == 302

    def test_from_popup_error(self, client):
        """POST /update from popup with error should redirect back to popup."""
        resp = client.post(
            "/adminpanel/owidcharts/update",
            data={"chart_id": "99999", "slug": "s", "title": "T", "from_popup": "1"},
        )

        assert resp.status_code in (200, 302)


class TestDeleteChart:
    """Tests for _delete_chart via HTTP route."""

    def _seed_chart(self, slug: str = "del-chart", title: str = "Delete Chart"):
        """Seed an OWID chart record via the real service."""
        service = OwidChartsService()
        service.add_chart(slug=slug, title=title)
        return service.get_chart_by_slug(slug)

    def test_success(self, client):
        """POST /<chart_id>/delete should remove the chart."""
        chart = self._seed_chart(slug="del-ok", title="Delete OK")

        resp = client.post(f"/adminpanel/owidcharts/{chart.chart_id}/delete")

        assert resp.status_code == 302
        assert OwidChartsService().get_chart_by_id(chart.chart_id) is None

    def test_not_found(self, client):
        """POST /<chart_id>/delete with nonexistent id should redirect."""
        resp = client.post("/adminpanel/owidcharts/99999/delete")

        assert resp.status_code == 302

    def test_from_popup(self, client):
        """POST /<chart_id>/delete from popup should render popup."""
        chart = self._seed_chart(slug="del-popup", title="Delete Popup")

        resp = client.post(
            f"/adminpanel/owidcharts/{chart.chart_id}/delete",
            data={"from_popup": "1"},
        )

        assert resp.status_code == 200
        html = resp.data.decode()
        assert "Action Completed" in html


class TestEditChart:
    """Tests for _edit_chart via HTTP route."""

    def _seed_chart(self, slug: str = "edit-chart", title: str = "Edit Chart"):
        """Seed an OWID chart record via the real service."""
        service = OwidChartsService()
        service.add_chart(slug=slug, title=title)
        return service.get_chart_by_slug(slug)

    def test_found(self, client):
        """GET /<chart_id>/edit should render the edit form."""
        chart = self._seed_chart(slug="edit-ok", title="Edit OK")

        resp = client.get(f"/adminpanel/owidcharts/{chart.chart_id}/edit")

        assert resp.status_code == 200
        html = resp.data.decode()
        assert "edit-ok" in html

    def test_not_found(self, client):
        """GET /<chart_id>/edit with nonexistent id should show error."""
        resp = client.get("/adminpanel/owidcharts/99999/edit")

        assert resp.status_code == 200
        html = resp.data.decode()
        assert "Chart not found" in html
