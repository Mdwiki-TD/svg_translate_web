"""
Unit tests for src/main_app/adminpanel/routes/coordinators.py module.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.main_app.database.services import AdminService, UsersService


@pytest.fixture(autouse=True)
def _fake_admin_user(monkeypatch):
    """Fake an authenticated admin user for all tests in this module."""
    admin_user = SimpleNamespace(username="test_admin", is_active_admin=True)
    monkeypatch.setattr("src.main_app.admin.decorators.get_current_user", lambda: admin_user)
    monkeypatch.setattr("src.main_app.public.auth.utils.get_current_user", lambda: admin_user)
    monkeypatch.setattr("src.main_app.public.utils.routes_utils.get_current_user", lambda: admin_user)


@pytest.fixture
def client(mock_app):
    """Test client bound to mock_app."""
    return mock_app.test_client()


class TestCoordinatorDashboard:
    """Tests for the coordinator dashboard."""

    def _seed_coordinator(self, username: str = "coord1", is_active: bool = True):
        """Seed a coordinator via real services."""
        UsersService().create_user(username)
        admin_service = AdminService()
        admin_service.add_coordinator(username)
        if not is_active:
            record = admin_service.get_record_by_id(
                admin_service.session.query(admin_service.model)
                .filter(admin_service.model.username == username)
                .first()
                .id
            )
            admin_service.set_coordinator_active(record.id, False)
        return admin_service.session.query(admin_service.model).filter(admin_service.model.username == username).first()

    def test_dashboard_requires_auth(self, client, mock_app):
        """Dashboard should return 200 for authenticated admin."""
        resp = client.get("/adminpanel/coordinators/")

        assert resp.status_code == 200

    def test_renders_with_coordinators(self, client):
        """Dashboard should list coordinators."""
        self._seed_coordinator("coord_active", is_active=True)

        resp = client.get("/adminpanel/coordinators/")

        assert resp.status_code == 200
        html = resp.data.decode()
        assert "coord_active" in html

    def test_renders_with_empty_list(self, client):
        """Dashboard should render with no coordinators."""
        resp = client.get("/adminpanel/coordinators/")

        assert resp.status_code == 200


class TestAddCoordinator:
    """Tests for adding a coordinator."""

    def _seed_user(self, username: str = "new_user"):
        """Seed a user record for foreign key."""
        UsersService().create_user(username)

    def test_missing_username(self, client):
        """POST /add with empty username should redirect."""
        resp = client.post(
            "/adminpanel/coordinators/add",
            data={"username": ""},
        )

        assert resp.status_code == 302

    def test_user_not_found(self, client):
        """POST /add with non-existent user should redirect."""
        resp = client.post(
            "/adminpanel/coordinators/add",
            data={"username": "unknown_user"},
        )

        assert resp.status_code == 302

    def test_duplicate_user(self, client):
        """POST /add with existing coordinator should redirect."""
        self._seed_user("existing_user")
        admin_service = AdminService()
        admin_service.add_coordinator("existing_user")

        resp = client.post(
            "/adminpanel/coordinators/add",
            data={"username": "existing_user"},
        )

        assert resp.status_code == 302

    def test_success(self, client):
        """POST /add with valid new user should create coordinator."""
        self._seed_user("new_coord")

        resp = client.post(
            "/adminpanel/coordinators/add",
            data={"username": "new_coord"},
        )

        assert resp.status_code == 302
        admin_service = AdminService()
        coordinators = admin_service.list_coordinators()
        assert any(c.username == "new_coord" for c in coordinators)


class TestSetRecordActiveStatus:
    """Tests for activating/deactivating coordinators."""

    def _seed_coordinator(self, username: str = "toggle_coord"):
        """Seed a coordinator via real services."""
        UsersService().create_user(username)
        return AdminService().add_coordinator(username)

    def test_activate_success(self, client):
        """POST /<id>/activate should set is_active=True."""
        coord = self._seed_coordinator("activate_coord")
        AdminService().set_coordinator_active(coord.id, False)

        resp = client.post(f"/adminpanel/coordinators/{coord.id}/activate")

        assert resp.status_code == 302
        updated = AdminService().get_record_by_id(coord.id)
        assert updated.is_active is True

    def test_deactivate_success(self, client):
        """POST /<id>/deactivate should set is_active=False."""
        coord = self._seed_coordinator("deactivate_coord")

        resp = client.post(f"/adminpanel/coordinators/{coord.id}/deactivate")

        assert resp.status_code == 302
        updated = AdminService().get_record_by_id(coord.id)
        assert updated.is_active is False

    def test_not_found(self, client):
        """POST /<id>/activate with nonexistent id should redirect."""
        resp = client.post("/adminpanel/coordinators/99999/activate")

        assert resp.status_code == 302


class TestDeleteCoordinator:
    """Tests for deleting a coordinator."""

    def _seed_coordinator(self, username: str = "del_coord"):
        """Seed a coordinator via real services."""
        UsersService().create_user(username)
        return AdminService().add_coordinator(username)

    def test_success(self, client):
        """POST /<id>/delete should remove the coordinator."""
        coord = self._seed_coordinator("del_coord_ok")

        resp = client.post(f"/adminpanel/coordinators/{coord.id}/delete")

        assert resp.status_code == 302
        assert AdminService().get_record_by_id(coord.id) is None

    def test_not_found(self, client):
        """POST /<id>/delete with nonexistent id should redirect."""
        resp = client.post("/adminpanel/coordinators/99999/delete")

        assert resp.status_code == 302
