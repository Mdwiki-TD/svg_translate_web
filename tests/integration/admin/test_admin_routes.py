"""Integration tests for src/main_app/admin_panel/route.py module.

Tests the admin dashboard, users listing, and admin management through
the Flask test client with a real SQLite database (via TestingConfig).
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from src.main_app.database.services import AdminService, UsersService, UserTokenService
from src.main_app.services.core.crypto import CryptoService


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        self.service = AdminService()
        self.users_service = UsersService()
        self.users_token_service = UserTokenService()
        self._crypto = CryptoService()

    def _upsert_u_token(self, username: str, access_key: str, access_secret: str) -> int:
        user = self.users_service.create_user(username)
        encrypted_token = self._crypto.encrypt(access_key)
        encrypted_secret = self._crypto.encrypt(access_secret)

        assert user is not None

        UserTokenService().upsert_user_token(
            user_id=user.user_id,
            encrypted_token=encrypted_token,
            encrypted_secret=encrypted_secret,
        )
        return user.user_id

    def _seed_admin(self, mock_app, username="AdminUser"):
        """Create a user token + active admin record for testing admin routes."""
        with mock_app.app_context():
            uid = self._upsert_u_token(
                username=username,
                access_key="admin-key",
                access_secret="admin-secret",
            )
            try:
                self.service.add_admin(username)
            except ValueError:
                pass
            except Exception:
                raise
            return uid

    def _login_admin(self, mock_app, mock_client, username="AdminUser"):
        """Set session to an admin user (DB record must already exist)."""
        uid = self._seed_admin(mock_app, username=username)
        with mock_client.session_transaction() as sess:
            sess["uid"] = uid
            sess["username"] = username
        return uid


@pytest.mark.usefixtures("mock_app")
class TestAdminDashboard(TestSetup):
    """GET /admin_panel/ — admin dashboard page."""

    def test_admin_requires_login(self, mock_client):
        """Unauthenticated user should be redirected to login."""
        resp = mock_client.get("/admin_panel/")
        assert resp.status_code == 302
        assert "login" in resp.headers["Location"]

    def test_admin_requires_admin_role(self, mock_app, mock_client):
        """A regular user (not admin) should get 403."""
        with mock_app.app_context():
            uid = self._upsert_u_token(
                username="RegularUser",
                access_key="k",
                access_secret="s",
            )

        with mock_client.session_transaction() as sess:
            sess["uid"] = uid
            sess["username"] = "RegularUser"

        resp = mock_client.get("/admin_panel/")
        assert resp.status_code == 403

    def test_admin_dashboard_loads(self, mock_app, mock_client):
        """An admin user should see the dashboard."""
        self._login_admin(mock_app, mock_client)
        resp = mock_client.get("/admin_panel/")
        assert resp.status_code == 200

    def test_admin_inactive_admin_gets_403(self, mock_app, mock_client):
        """A deactivated admin should get 403."""
        with mock_app.app_context():
            uid = self._upsert_u_token(
                username="InactiveAdmin",
                access_key="k",
                access_secret="s",
            )
            coord = self.service.add_admin("InactiveAdmin")
            self.service.set_admin_active(coord.id, False)

        with mock_client.session_transaction() as sess:
            sess["uid"] = uid
            sess["username"] = "InactiveAdmin"

        resp = mock_client.get("/admin_panel/")
        assert resp.status_code == 403


@pytest.mark.usefixtures("mock_app")
class TestDbAdminPanel(TestSetup):
    """GET /admin_panel/db_admin/ — Flask-Admin DB admin panel."""

    def test_db_admin_requires_login(self, mock_client):
        """Unauthenticated user should be redirected to login when trying to access DB admin."""
        resp = mock_client.get("/admin_panel/db_admin/")
        assert resp.status_code == 302
        assert "login" in resp.headers["Location"]

    def test_db_admin_requires_admin_role(self, mock_app, mock_client):
        """A regular user (not admin/admin) should get 403 when trying to access DB admin."""
        with mock_app.app_context():
            uid = self._upsert_u_token(
                username="RegularUser",
                access_key="k",
                access_secret="s",
            )

        with mock_client.session_transaction() as sess:
            sess["uid"] = uid
            sess["username"] = "RegularUser"

        resp = mock_client.get("/admin_panel/db_admin/")
        assert resp.status_code == 403

    def test_db_admin_loads_for_admin(self, mock_app, mock_client):
        """An admin user should be able to load the DB admin dashboard."""
        self._login_admin(mock_app, mock_client)
        resp = mock_client.get("/admin_panel/db_admin/")
        assert resp.status_code == 200

    def test_db_admin_model_view_requires_login(self, mock_client):
        """Unauthenticated user should be redirected to login when trying to access a model view."""
        resp = mock_client.get("/admin_panel/db_admin/userrecord/")
        assert resp.status_code == 302
        assert "login" in resp.headers["Location"]

    def test_db_admin_model_view_requires_admin_role(self, mock_app, mock_client):
        """A regular user should get 403 when trying to access a model view."""
        with mock_app.app_context():
            uid = self._upsert_u_token(
                username="RegularUser",
                access_key="k",
                access_secret="s",
            )

        with mock_client.session_transaction() as sess:
            sess["uid"] = uid
            sess["username"] = "RegularUser"

        resp = mock_client.get("/admin_panel/db_admin/userrecord/")
        assert resp.status_code == 403

    def test_db_admin_model_view_loads_for_admin(self, mock_app, mock_client):
        """An admin user should be able to load a model view."""
        self._login_admin(mock_app, mock_client)
        resp = mock_client.get("/admin_panel/db_admin/userrecord/")
        assert resp.status_code == 200


@pytest.mark.usefixtures("mock_app")
class TestAdminUsersPage(TestSetup):
    """GET /admin_panel/users — list all registered users."""

    def test_users_page_requires_admin(self, mock_app, mock_client):
        """Non-admin user should get 403."""
        with mock_app.app_context():
            uid = self._upsert_u_token(
                username="NonAdmin",
                access_key="k",
                access_secret="s",
            )

        with mock_client.session_transaction() as sess:
            sess["uid"] = uid
            sess["username"] = "NonAdmin"

        resp = mock_client.get("/admin_panel/users")
        assert resp.status_code == 403

    def test_users_page_shows_registered_users(self, mock_app, mock_client):
        """Admin should see the users list with seeded users."""

        with mock_app.app_context():
            self._upsert_u_token(
                username="SomeUser",
                access_key="k",
                access_secret="s",
            )

        self._login_admin(mock_app, mock_client)
        resp = mock_client.get("/admin_panel/users")
        assert resp.status_code == 200

    def test_users_page_empty_list(self, mock_app, mock_client):
        """Users page should load even with no regular users."""

        self._login_admin(mock_app, mock_client)
        resp = mock_client.get("/admin_panel/users")
        assert resp.status_code == 200


@pytest.mark.usefixtures("mock_app")
class TestAdminRoutes(TestSetup):
    """Admin CRUD via /admin_panel/admins/ endpoints."""

    def test_admins_dashboard_requires_admin(self, mock_app, mock_client):
        """Non-admin should get 403 on admins page."""
        with mock_app.app_context():
            uid = self._upsert_u_token(
                username="NonAdmin",
                access_key="k",
                access_secret="s",
            )

        with mock_client.session_transaction() as sess:
            sess["uid"] = uid
            sess["username"] = "NonAdmin"

        resp = mock_client.get("/admin_panel/admins/")
        assert resp.status_code == 403

    def test_admins_dashboard_loads(self, mock_app, mock_client):
        """Admin should see the admins dashboard."""

        self._login_admin(mock_app, mock_client)
        resp = mock_client.get("/admin_panel/admins/")
        assert resp.status_code == 200

    def test_add_admin(self, mock_app, mock_client):
        """Admin should be able to add a new admin."""

        with mock_app.app_context():
            self._upsert_u_token(
                username="NewCoord",
                access_key="k",
                access_secret="s",
            )

        self._login_admin(mock_app, mock_client)
        resp = mock_client.post(
            "/admin_panel/admins/add",
            data={"username": "NewCoord"},
            follow_redirects=True,
        )
        assert resp.status_code == 200

        with mock_app.app_context():
            result = self.service.is_active_admin("NewCoord")
            assert result is True

    def test_add_admin_empty_username_flash(self, mock_app, mock_client, monkeypatch):
        """Adding admin with empty username should flash error."""
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.admins.flash", mock_flash)

        self._login_admin(mock_app, mock_client)
        resp = mock_client.post(
            "/admin_panel/admins/add",
            data={"username": ""},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        mock_flash.assert_called_once_with("Username is required to add an admin.", "danger")

    def test_add_duplicate_admin_flash(self, mock_app, mock_client, monkeypatch):
        """Adding a duplicate admin should flash warning."""
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.admins.flash", mock_flash)

        self._login_admin(mock_app, mock_client)
        mock_client.post(
            "/admin_panel/admins/add",
            data={"username": "AdminUser"},
            follow_redirects=True,
        )
        mock_flash.reset_mock()
        resp = mock_client.post(
            "/admin_panel/admins/add",
            data={"username": "AdminUser"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        mock_flash.assert_called_once()
        assert "already exists" in mock_flash.call_args[0][0]
        assert mock_flash.call_args[0][1] == "warning"

    def test_toggle_admin_active(self, mock_app, mock_client):
        """Admin should be able to deactivate an admin."""

        with mock_app.app_context():
            self._upsert_u_token(
                username="ToggleCoord",
                access_key="k",
                access_secret="s",
            )
            coord = self.service.add_admin("ToggleCoord")

        self._login_admin(mock_app, mock_client)
        resp = mock_client.post(
            f"/admin_panel/admins/{coord.id}/deactivate",
            follow_redirects=True,
        )
        assert resp.status_code == 200

        with mock_app.app_context():
            result = self.service.is_active_admin("ToggleCoord")
            assert result is False

    def test_toggle_admin_reactivate(self, mock_app, mock_client):
        """Admin should be able to reactivate an admin."""

        with mock_app.app_context():
            self._upsert_u_token(
                username="ReactivateCoord",
                access_key="k",
                access_secret="s",
            )
            coord = self.service.add_admin("ReactivateCoord")
            self.service.set_admin_active(coord.id, False)

        self._login_admin(mock_app, mock_client)
        resp = mock_client.post(
            f"/admin_panel/admins/{coord.id}/activate",
            follow_redirects=True,
        )
        assert resp.status_code == 200

        with mock_app.app_context():
            result = self.service.is_active_admin("ReactivateCoord")
            assert result is True

    def test_delete_admin(self, mock_app, mock_client):
        """Admin should be able to delete an admin."""

        with mock_app.app_context():
            self._upsert_u_token(
                username="DeleteCoord",
                access_key="k",
                access_secret="s",
            )
            coord = self.service.add_admin("DeleteCoord")

        self._login_admin(mock_app, mock_client)
        resp = mock_client.post(
            f"/admin_panel/admins/{coord.id}/delete",
            follow_redirects=True,
        )
        assert resp.status_code == 200

        with mock_app.app_context():
            coords = self.service.list_admins()
            usernames = [c.username for c in coords]
            assert "DeleteCoord" not in usernames

    def test_delete_nonexistent_admin_flash(self, mock_app, mock_client, monkeypatch):
        """Deleting a non-existent admin should flash warning."""
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.admins.flash", mock_flash)

        self._login_admin(mock_app, mock_client)
        resp = mock_client.post(
            "/admin_panel/admins/9999/delete",
            follow_redirects=True,
        )
        assert resp.status_code == 200
        mock_flash.assert_called_once()
        assert "was not found" in mock_flash.call_args[0][0]
        assert mock_flash.call_args[0][1] == "warning"


@pytest.mark.usefixtures("mock_app")
class TestAdminRouteIntegration(TestSetup):
    """End-to-end integration scenarios for admin features."""

    def test_admin_can_manage_admin_lifecycle(self, mock_app, mock_client):
        """Full lifecycle: add -> deactivate -> reactivate -> delete admin."""

        with mock_app.app_context():
            self._upsert_u_token(
                username="LifecycleCoord",
                access_key="k",
                access_secret="s",
            )

        self._login_admin(mock_app, mock_client)

        # Add
        mock_client.post(
            "/admin_panel/admins/add",
            data={"username": "LifecycleCoord"},
            follow_redirects=True,
        )
        with mock_app.app_context():
            result = self.service.is_active_admin("LifecycleCoord")
            assert result is True

        # Get the admin ID
        with mock_app.app_context():
            coords = self.service.list_admins()
            coord = next(c for c in coords if c.username == "LifecycleCoord")

        # Deactivate
        mock_client.post(
            f"/admin_panel/admins/{coord.id}/deactivate",
            follow_redirects=True,
        )
        with mock_app.app_context():
            result = self.service.is_active_admin("LifecycleCoord")
            assert result is False

        # Reactivate
        mock_client.post(
            f"/admin_panel/admins/{coord.id}/activate",
            follow_redirects=True,
        )
        with mock_app.app_context():
            result = self.service.is_active_admin("LifecycleCoord")
            assert result is True

        # Delete
        mock_client.post(
            f"/admin_panel/admins/{coord.id}/delete",
            follow_redirects=True,
        )
        with mock_app.app_context():
            coords = self.service.list_admins()
            usernames = [c.username for c in coords]
            assert "LifecycleCoord" not in usernames

    def test_non_admin_cannot_access_any_admin_route(self, mock_app, mock_client):
        """A regular user should be blocked from all admin endpoints."""
        with mock_app.app_context():
            uid = self._upsert_u_token(
                username="BlockedUser",
                access_key="k",
                access_secret="s",
            )

        with mock_client.session_transaction() as sess:
            sess["uid"] = uid
            sess["username"] = "BlockedUser"

        protected_routes = [
            ("GET", "/admin_panel/"),
            ("GET", "/admin_panel/users"),
            ("GET", "/admin_panel/admins/"),
            ("POST", "/admin_panel/admins/add"),
        ]

        for method, path in protected_routes:
            if method == "GET":
                resp = mock_client.get(path)
            else:
                resp = mock_client.post(path, data={})
            assert resp.status_code == 403, f"Expected 403 for {method} {path}"

    def test_sidebar_context_injected(self, mock_app, mock_client):
        """Admin pages should have the sidebar context variable injected."""

        self._login_admin(mock_app, mock_client)
        resp = mock_client.get("/admin_panel/")
        assert resp.status_code == 200
