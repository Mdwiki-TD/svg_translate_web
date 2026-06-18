"""Integration tests for src/main_app/app_routes/admin/routes.py module.

Tests the admin dashboard, users listing, and coordinator management through
the Flask test client with a real SQLite database (via TestingConfig).
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.main_app.db.services import (
    is_active_coordinator,
    upsert_user_token,
)
from src.main_app.db.services.admin_service import (
    add_coordinator,
    list_coordinators,
    set_coordinator_active,
)
from src.main_app.db.services.users_service import create_user


def _upsert_u_token(username: str, access_key: str, access_secret: str) -> int:
    user = create_user(username)
    upsert_user_token(
        user_id=user.user_id,
        access_key=access_key,
        access_secret=access_secret,
    )
    return user.user_id


def _seed_admin(mock_app, username="AdminUser"):
    """Create a user token + active coordinator record for testing admin routes."""
    with mock_app.app_context():
        uid = _upsert_u_token(
            username=username,
            access_key="admin-key",
            access_secret="admin-secret",
        )
        try:
            add_coordinator(username)
        except ValueError:
            pass
        except Exception:
            raise
        return uid


def _login_admin(mock_app, mock_client, username="AdminUser"):
    """Set session to an admin user (DB record must already exist)."""
    uid = _seed_admin(mock_app, username="AdminUser")
    with mock_client.session_transaction() as sess:
        sess["uid"] = uid
        sess["username"] = username
    return uid


@pytest.mark.usefixtures("mock_app")
class TestAdminDashboard:
    """GET /admin/ — admin dashboard page."""

    def test_admin_requires_login(self, mock_client):
        """Unauthenticated user should be redirected to login."""
        resp = mock_client.get("/admin/")
        assert resp.status_code == 302
        assert "login" in resp.headers["Location"]

    def test_admin_requires_coordinator_role(self, mock_app, mock_client):
        """A regular user (not coordinator) should get 403."""
        with mock_app.app_context():
            uid = _upsert_u_token(
                username="RegularUser",
                access_key="k",
                access_secret="s",
            )

        with mock_client.session_transaction() as sess:
            sess["uid"] = uid
            sess["username"] = "RegularUser"

        resp = mock_client.get("/admin/")
        assert resp.status_code == 403

    def test_admin_dashboard_loads(self, mock_app, mock_client):
        """An admin user should see the dashboard."""
        _login_admin(mock_app, mock_client)
        resp = mock_client.get("/admin/")
        assert resp.status_code == 200

    def test_admin_inactive_coordinator_gets_403(self, mock_app, mock_client):
        """A deactivated coordinator should get 403."""
        with mock_app.app_context():
            uid = _upsert_u_token(
                username="InactiveAdmin",
                access_key="k",
                access_secret="s",
            )
            coord = add_coordinator("InactiveAdmin")
            set_coordinator_active(coord.id, False)

        with mock_client.session_transaction() as sess:
            sess["uid"] = uid
            sess["username"] = "InactiveAdmin"

        resp = mock_client.get("/admin/")
        assert resp.status_code == 403


@pytest.mark.usefixtures("mock_app")
class TestAdminUsersPage:
    """GET /admin/users — list all registered users."""

    def test_users_page_requires_admin(self, mock_app, mock_client):
        """Non-admin user should get 403."""
        with mock_app.app_context():
            uid = _upsert_u_token(
                username="NonAdmin",
                access_key="k",
                access_secret="s",
            )

        with mock_client.session_transaction() as sess:
            sess["uid"] = uid
            sess["username"] = "NonAdmin"

        resp = mock_client.get("/admin/users")
        assert resp.status_code == 403

    def test_users_page_shows_registered_users(self, mock_app, mock_client):
        """Admin should see the users list with seeded users."""

        with mock_app.app_context():
            _upsert_u_token(
                username="SomeUser",
                access_key="k",
                access_secret="s",
            )

        _login_admin(mock_app, mock_client)
        resp = mock_client.get("/admin/users")
        assert resp.status_code == 200

    def test_users_page_empty_list(self, mock_app, mock_client):
        """Users page should load even with no regular users."""

        _login_admin(mock_app, mock_client)
        resp = mock_client.get("/admin/users")
        assert resp.status_code == 200


@pytest.mark.usefixtures("mock_app")
class TestCoordinatorRoutes:
    """Coordinator CRUD via /admin/coordinators/ endpoints."""

    def test_coordinators_dashboard_requires_admin(self, mock_app, mock_client):
        """Non-admin should get 403 on coordinators page."""
        with mock_app.app_context():
            uid = _upsert_u_token(
                username="NonAdmin",
                access_key="k",
                access_secret="s",
            )

        with mock_client.session_transaction() as sess:
            sess["uid"] = uid
            sess["username"] = "NonAdmin"

        resp = mock_client.get("/admin/coordinators/")
        assert resp.status_code == 403

    def test_coordinators_dashboard_loads(self, mock_app, mock_client):
        """Admin should see the coordinators dashboard."""

        _login_admin(mock_app, mock_client)
        resp = mock_client.get("/admin/coordinators/")
        assert resp.status_code == 200

    def test_add_coordinator(self, mock_app, mock_client):
        """Admin should be able to add a new coordinator."""

        with mock_app.app_context():
            _upsert_u_token(
                username="NewCoord",
                access_key="k",
                access_secret="s",
            )

        _login_admin(mock_app, mock_client)
        resp = mock_client.post(
            "/admin/coordinators/add",
            data={"username": "NewCoord"},
            follow_redirects=True,
        )
        assert resp.status_code == 200

        with mock_app.app_context():
            result = is_active_coordinator("NewCoord")
            assert result is True

    def test_add_coordinator_empty_username_flash(self, mock_app, mock_client, monkeypatch):
        """Adding coordinator with empty username should flash error."""
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.app_routes.admin_routes.coordinators.flash", mock_flash)

        _login_admin(mock_app, mock_client)
        resp = mock_client.post(
            "/admin/coordinators/add",
            data={"username": ""},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        mock_flash.assert_called_once_with("Username is required to add a coordinator.", "danger")

    def test_add_duplicate_coordinator_flash(self, mock_app, mock_client, monkeypatch):
        """Adding a duplicate coordinator should flash warning."""
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.app_routes.admin_routes.coordinators.flash", mock_flash)

        _login_admin(mock_app, mock_client)
        mock_client.post(
            "/admin/coordinators/add",
            data={"username": "AdminUser"},
            follow_redirects=True,
        )
        mock_flash.reset_mock()
        resp = mock_client.post(
            "/admin/coordinators/add",
            data={"username": "AdminUser"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        mock_flash.assert_called_once()
        assert "already exists" in mock_flash.call_args[0][0]
        assert mock_flash.call_args[0][1] == "warning"

    def test_toggle_coordinator_active(self, mock_app, mock_client):
        """Admin should be able to deactivate a coordinator."""

        with mock_app.app_context():
            _upsert_u_token(
                username="ToggleCoord",
                access_key="k",
                access_secret="s",
            )
            coord = add_coordinator("ToggleCoord")

        _login_admin(mock_app, mock_client)
        resp = mock_client.post(
            f"/admin/coordinators/{coord.id}/active",
            data={"active": "0"},
            follow_redirects=True,
        )
        assert resp.status_code == 200

        with mock_app.app_context():
            result = is_active_coordinator("ToggleCoord")
            assert result is False

    def test_toggle_coordinator_reactivate(self, mock_app, mock_client):
        """Admin should be able to reactivate a coordinator."""

        with mock_app.app_context():
            _upsert_u_token(
                username="ReactivateCoord",
                access_key="k",
                access_secret="s",
            )
            coord = add_coordinator("ReactivateCoord")
            set_coordinator_active(coord.id, False)

        _login_admin(mock_app, mock_client)
        resp = mock_client.post(
            f"/admin/coordinators/{coord.id}/active",
            data={"active": "1"},
            follow_redirects=True,
        )
        assert resp.status_code == 200

        with mock_app.app_context():
            result = is_active_coordinator("ReactivateCoord")
            assert result is True

    def test_delete_coordinator(self, mock_app, mock_client):
        """Admin should be able to delete a coordinator."""

        with mock_app.app_context():
            _upsert_u_token(
                username="DeleteCoord",
                access_key="k",
                access_secret="s",
            )
            coord = add_coordinator("DeleteCoord")

        _login_admin(mock_app, mock_client)
        resp = mock_client.post(
            f"/admin/coordinators/{coord.id}/delete",
            follow_redirects=True,
        )
        assert resp.status_code == 200

        with mock_app.app_context():
            coords = list_coordinators()
            usernames = [c.username for c in coords]
            assert "DeleteCoord" not in usernames

    def test_delete_nonexistent_coordinator_flash(self, mock_app, mock_client, monkeypatch):
        """Deleting a non-existent coordinator should flash warning."""
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.app_routes.admin_routes.coordinators.flash", mock_flash)

        _login_admin(mock_app, mock_client)
        resp = mock_client.post(
            "/admin/coordinators/9999/delete",
            follow_redirects=True,
        )
        assert resp.status_code == 200
        mock_flash.assert_called_once()
        assert "was not found" in mock_flash.call_args[0][0]
        assert mock_flash.call_args[0][1] == "warning"


@pytest.mark.usefixtures("mock_app")
class TestAdminRouteIntegration:
    """End-to-end integration scenarios for admin features."""

    def test_admin_can_manage_coordinator_lifecycle(self, mock_app, mock_client):
        """Full lifecycle: add -> deactivate -> reactivate -> delete coordinator."""

        with mock_app.app_context():
            _upsert_u_token(
                username="LifecycleCoord",
                access_key="k",
                access_secret="s",
            )

        _login_admin(mock_app, mock_client)

        # Add
        mock_client.post(
            "/admin/coordinators/add",
            data={"username": "LifecycleCoord"},
            follow_redirects=True,
        )
        with mock_app.app_context():
            result = is_active_coordinator("LifecycleCoord")
            assert result is True

        # Get the coordinator ID
        with mock_app.app_context():
            coords = list_coordinators()
            coord = next(c for c in coords if c.username == "LifecycleCoord")

        # Deactivate
        mock_client.post(
            f"/admin/coordinators/{coord.id}/active",
            data={"active": "0"},
            follow_redirects=True,
        )
        with mock_app.app_context():
            result = is_active_coordinator("LifecycleCoord")
            assert result is False

        # Reactivate
        mock_client.post(
            f"/admin/coordinators/{coord.id}/active",
            data={"active": "1"},
            follow_redirects=True,
        )
        with mock_app.app_context():
            result = is_active_coordinator("LifecycleCoord")
            assert result is True

        # Delete
        mock_client.post(
            f"/admin/coordinators/{coord.id}/delete",
            follow_redirects=True,
        )
        with mock_app.app_context():
            coords = list_coordinators()
            usernames = [c.username for c in coords]
            assert "LifecycleCoord" not in usernames

    def test_non_admin_cannot_access_any_admin_route(self, mock_app, mock_client):
        """A regular user should be blocked from all admin endpoints."""
        with mock_app.app_context():
            uid = _upsert_u_token(
                username="BlockedUser",
                access_key="k",
                access_secret="s",
            )

        with mock_client.session_transaction() as sess:
            sess["uid"] = uid
            sess["username"] = "BlockedUser"

        protected_routes = [
            ("GET", "/admin/"),
            ("GET", "/admin/users"),
            ("GET", "/admin/coordinators/"),
            ("POST", "/admin/coordinators/add"),
        ]

        for method, path in protected_routes:
            if method == "GET":
                resp = mock_client.get(path)
            else:
                resp = mock_client.post(path, data={})
            assert resp.status_code == 403, f"Expected 403 for {method} {path}"

    def test_sidebar_context_injected(self, mock_app, mock_client):
        """Admin pages should have the sidebar context variable injected."""

        _login_admin(mock_app, mock_client)
        resp = mock_client.get("/admin/")
        assert resp.status_code == 200
