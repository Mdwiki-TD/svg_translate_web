"""
Unit tests for src/main_app/admin_panel/routes/admins.py module.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from src.main_app.database.services import AdminService, UsersService


@pytest.fixture(autouse=True)
def _fake_admin_user(monkeypatch):
    """Fake an authenticated admin user for all tests in this module."""
    admin_user = SimpleNamespace(username="test_admin", is_active_admin=True)
    monkeypatch.setattr(
        "src.main_app.decorators.admin_decorators.CurrentUserResolver.get_current_user", lambda: admin_user
    )
    monkeypatch.setattr(
        "src.main_app.decorators.auth_decorators.CurrentUserResolver.get_current_user", lambda: admin_user
    )
    monkeypatch.setattr("src.main_app.public.routes_utils.CurrentUserResolver.get_current_user", lambda: admin_user)


@pytest.fixture
def client(mock_app):
    """Test client bound to mock_app."""
    return mock_app.test_client()


class TestAdminDashboard:
    """Tests for the admin dashboard."""

    def _seed_admin(self, username: str = "coord1", is_active: bool = True):
        """Seed an admin via real services."""
        UsersService().create_user(username)
        admin_service = AdminService()
        admin_service.add_admin(username)
        if not is_active:
            record = admin_service.get_record_by_id(
                admin_service.session.query(admin_service.model)
                .filter(admin_service.model.username == username)
                .first()
                .id
            )
            admin_service.set_admin_active(record.id, False)
        return admin_service.session.query(admin_service.model).filter(admin_service.model.username == username).first()

    def test_dashboard_requires_auth(self, client, mock_app):
        """Dashboard should return 200 for authenticated admin."""
        resp = client.get("/admin_panel/admins/")

        assert resp.status_code == 200

    def test_renders_with_admins(self, client):
        """Dashboard should list admins."""
        self._seed_admin("coord_active", is_active=True)

        resp = client.get("/admin_panel/admins/")

        assert resp.status_code == 200
        html = resp.data.decode()
        assert "coord_active" in html

    def test_renders_with_empty_list(self, client):
        """Dashboard should render with no admins."""
        resp = client.get("/admin_panel/admins/")

        assert resp.status_code == 200


class TestAddAdmin:
    """Tests for adding an admin."""

    def _seed_user(self, username: str = "new_user"):
        """Seed a user record for foreign key."""
        UsersService().create_user(username)

    def test_missing_username(self, client):
        """POST /add with empty username should redirect."""
        resp = client.post(
            "/admin_panel/admins/add",
            data={"username": ""},
        )

        assert resp.status_code == 302

    def test_user_not_found(self, client):
        """POST /add with non-existent user should redirect."""
        resp = client.post(
            "/admin_panel/admins/add",
            data={"username": "unknown_user"},
        )

        assert resp.status_code == 302

    def test_duplicate_user(self, client):
        """POST /add with existing admin should redirect."""
        self._seed_user("existing_user")
        admin_service = AdminService()
        admin_service.add_admin("existing_user")

        resp = client.post(
            "/admin_panel/admins/add",
            data={"username": "existing_user"},
        )

        assert resp.status_code == 302

    def test_success(self, client):
        """POST /add with valid new user should create admin."""
        self._seed_user("new_coord")

        resp = client.post(
            "/admin_panel/admins/add",
            data={"username": "new_coord"},
        )

        assert resp.status_code == 302
        admin_service = AdminService()
        admins = admin_service.list_admins()
        assert any(c.username == "new_coord" for c in admins)


class TestSetRecordActiveStatus:
    """Tests for activating/deactivating admins."""

    def _seed_admin(self, username: str = "toggle_coord"):
        """Seed an admin via real services."""
        UsersService().create_user(username)
        return AdminService().add_admin(username)

    def test_activate_success(self, client):
        """POST /<id>/activate should set is_active=True."""
        coord = self._seed_admin("activate_coord")
        AdminService().set_admin_active(coord.id, False)

        resp = client.post(f"/admin_panel/admins/{coord.id}/activate")

        assert resp.status_code == 302
        updated = AdminService().get_record_by_id(coord.id)
        assert updated.is_active is True

    def test_deactivate_success(self, client):
        """POST /<id>/deactivate should set is_active=False."""
        coord = self._seed_admin("deactivate_coord")

        resp = client.post(f"/admin_panel/admins/{coord.id}/deactivate")

        assert resp.status_code == 302
        updated = AdminService().get_record_by_id(coord.id)
        assert updated.is_active is False

    def test_not_found(self, client):
        """POST /<id>/activate with nonexistent id should redirect."""
        resp = client.post("/admin_panel/admins/99999/activate")

        assert resp.status_code == 302


class TestDeleteAdmin:
    """Tests for deleting an admin."""

    def _seed_admin(self, username: str = "del_coord"):
        """Seed an admin via real services."""
        UsersService().create_user(username)
        return AdminService().add_admin(username)

    def test_success(self, client):
        """POST /<id>/delete should remove the admin."""
        coord = self._seed_admin("del_coord_ok")

        resp = client.post(f"/admin_panel/admins/{coord.id}/delete")

        assert resp.status_code == 302
        assert AdminService().get_record_by_id(coord.id) is None

    def test_not_found(self, client):
        """POST /<id>/delete with nonexistent id should redirect."""
        resp = client.post("/admin_panel/admins/99999/delete")

        assert resp.status_code == 302
