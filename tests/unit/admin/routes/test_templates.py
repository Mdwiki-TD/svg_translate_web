"""Unit tests for src/main_app/adminpanel/routes/templates.py module."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.main_app.db.services import TemplateService


@pytest.fixture(autouse=True)
def _fake_admin_user(monkeypatch):
    """Fake an authenticated admin user for all tests in this module."""
    admin_user = SimpleNamespace(username="test_admin", is_active_admin=True)
    monkeypatch.setattr("src.main_app.admin.decorators.load_user", lambda: admin_user)
    monkeypatch.setattr("src.main_app.public.auth.utils.load_user", lambda: admin_user)
    monkeypatch.setattr("src.main_app.public.utils.routes_utils.load_user", lambda: admin_user)


@pytest.fixture
def client(mock_app):
    """Test client bound to mock_app."""
    return mock_app.test_client()


class TestTemplatesUnit:
    """Tests for TemplatesRoutesFuncs methods via HTTP routes with real DB/services."""

    def _seed_template(self, title: str = "T1", main_file: str = "f.svg", source: str = ""):
        """Seed a template record via the real service."""
        service = TemplateService()
        data = {"title": title, "main_file": main_file, "last_world_file": "", "source": source}
        service.add_template_data(data)
        return service.get_template_by_title(title)

    def test_create_json_file_success(self, client):
        """Download JSON should return a file with template data."""
        self._seed_template(title="T1", main_file="f.svg")

        resp = client.get("/adminpanel/templates/download-json")

        assert resp.status_code == 200
        assert "templates.json" in resp.headers.get("Content-Disposition", "")
        import json

        data = json.loads(resp.data)
        assert len(data) == 1
        assert data[0]["title"] == "T1"

    def test_create_json_file_no_templates(self, client):
        """Download JSON with no templates should redirect with warning."""
        resp = client.get("/adminpanel/templates/download-json")

        assert resp.status_code == 302

    def test_add_template_missing_title(self, client):
        """POST /add with empty title should redirect."""
        resp = client.post(
            "/adminpanel/templates/add",
            data={"title": "", "main_file": "f.svg", "last_world_file": "", "source": ""},
        )

        assert resp.status_code == 302

    def test_add_template_success(self, client):
        """POST /add with valid data should create the template."""
        resp = client.post(
            "/adminpanel/templates/add",
            data={"title": "NewT", "main_file": "f.svg", "last_world_file": "", "source": ""},
        )

        assert resp.status_code == 302
        assert TemplateService().get_template_by_title("NewT") is not None

    def test_add_template_value_error(self, client):
        """POST /add with duplicate title should redirect."""
        self._seed_template(title="Dup")

        resp = client.post(
            "/adminpanel/templates/add",
            data={"title": "Dup", "main_file": "", "last_world_file": "", "source": ""},
        )

        assert resp.status_code == 302

    def test_update_template_missing_id(self, client):
        """POST /update without id should redirect."""
        resp = client.post(
            "/adminpanel/templates/update",
            data={"title": "T", "main_file": "f.svg"},
        )

        assert resp.status_code == 302

    def test_update_template_success(self, client):
        """POST /update with valid data should update the template."""
        template = self._seed_template(title="UpdT", main_file="old.svg")

        resp = client.post(
            "/adminpanel/templates/update",
            data={"id": template.id, "title": "UpdT", "main_file": "new.svg", "from_popup": "0"},
        )

        assert resp.status_code == 302
        updated = TemplateService().get_template(template.id)
        assert updated.main_file == "new.svg"

    def test_update_template_not_found(self, client):
        """POST /update with nonexistent id should redirect."""
        resp = client.post(
            "/adminpanel/templates/update",
            data={"id": 99999, "title": "T", "main_file": "f.svg"},
        )

        assert resp.status_code == 302

    def test_update_template_from_popup(self, client):
        """POST /update with from_popup=1 should render popup."""
        template = self._seed_template(title="PopupT")

        resp = client.post(
            "/adminpanel/templates/update",
            data={"id": template.id, "title": "PopupT", "main_file": "f.svg", "from_popup": "1"},
        )

        assert resp.status_code == 200
        html = resp.data.decode()
        assert "Action Completed" in html

    def test_delete_template_success(self, client):
        """POST /<id>/delete should remove the template."""
        template = self._seed_template(title="DelT")

        resp = client.post(f"/adminpanel/templates/{template.id}/delete")

        assert resp.status_code == 302
        assert TemplateService().get_template(template.id) is None

    def test_delete_template_not_found(self, client):
        """POST /<id>/delete with nonexistent id should redirect."""
        resp = client.post("/adminpanel/templates/99999/delete")

        assert resp.status_code == 302

    def test_delete_template_from_popup(self, client):
        """POST /<id>/delete with from_popup=1 should render popup."""
        template = self._seed_template(title="DelPopupT")

        resp = client.post(
            f"/adminpanel/templates/{template.id}/delete",
            data={"from_popup": "1"},
        )

        assert resp.status_code == 200
        html = resp.data.decode()
        assert "Action Completed" in html

    def test_edit_template_found(self, client):
        """GET /<id>/edit should render the edit form."""
        template = self._seed_template(title="EditT")

        resp = client.get(f"/adminpanel/templates/{template.id}/edit")

        assert resp.status_code == 200
        html = resp.data.decode()
        assert "EditT" in html

    def test_edit_template_not_found(self, client):
        """GET /<id>/edit with nonexistent id should show error."""
        resp = client.get("/adminpanel/templates/99999/edit")

        assert resp.status_code == 200
        html = resp.data.decode()
        assert "Template not found" in html

    def test_edit_template_by_title_found(self, client):
        """GET /<title>/edit_by_title should render the edit form."""
        self._seed_template(title="TitleT")

        resp = client.get("/adminpanel/templates/TitleT/edit_by_title")

        assert resp.status_code == 200
        html = resp.data.decode()
        assert "TitleT" in html

    def test_edit_template_by_title_not_found(self, client):
        """GET /<title>/edit_by_title with nonexistent title should show error."""
        resp = client.get("/adminpanel/templates/Missing/edit_by_title")

        assert resp.status_code == 200
        html = resp.data.decode()
        assert "Template not found" in html
