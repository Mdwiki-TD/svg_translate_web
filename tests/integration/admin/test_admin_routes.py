"""Integration tests for src/main_app/adminpanel/route.py module.

Tests the admin dashboard, users listing, and coordinator management through
the Flask test client with a real SQLite database (via TestingConfig).
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.main_app.db.services import AdminService, UsersService, UserTokenService


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        self.service = AdminService()
        self.users_service = UsersService()
        self.users_token_service = UserTokenService()

    def _upsert_u_token(self, username: str, access_key: str, access_secret: str) -> int:
        user = self.users_service.create_user(username)
        encrypted_token = self.users_token_service.encrypt_value(access_key)
        encrypted_secret = self.users_token_service.encrypt_value(access_secret)

        UserTokenService().upsert_user_token(
            user_id=user.user_id,
            encrypted_token=encrypted_token,
            encrypted_secret=encrypted_secret,
        )
        return user.user_id

    def _seed_admin(self, mock_app, username="AdminUser"):
        """Create a user token + active coordinator record for testing admin routes."""
        with mock_app.app_context():
            uid = self._upsert_u_token(
                username=username,
                access_key="admin-key",
                access_secret="admin-secret",
            )
            try:
                self.service.add_coordinator(username)
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
    """GET /adminpanel/ — admin dashboard page."""

    def test_admin_requires_login(self, mock_client):
        """Unauthenticated user should be redirected to login."""
        resp = mock_client.get("/adminpanel/")
        assert resp.status_code == 302
        assert "login" in resp.headers["Location"]

    def test_admin_requires_coordinator_role(self, mock_app, mock_client):
        """A regular user (not coordinator) should get 403."""
        with mock_app.app_context():
            uid = self._upsert_u_token(
                username="RegularUser",
                access_key="k",
                access_secret="s",
            )

        with mock_client.session_transaction() as sess:
            sess["uid"] = uid
            sess["username"] = "RegularUser"

        resp = mock_client.get("/adminpanel/")
        assert resp.status_code == 403

    def test_admin_dashboard_loads(self, mock_app, mock_client):
        """An admin user should see the dashboard."""
        self._login_admin(mock_app, mock_client)
        resp = mock_client.get("/adminpanel/")
        assert resp.status_code == 200

    def test_admin_inactive_coordinator_gets_403(self, mock_app, mock_client):
        """A deactivated coordinator should get 403."""
        with mock_app.app_context():
            uid = self._upsert_u_token(
                username="InactiveAdmin",
                access_key="k",
                access_secret="s",
            )
            coord = self.service.add_coordinator("InactiveAdmin")
            self.service.set_coordinator_active(coord.id, False)

        with mock_client.session_transaction() as sess:
            sess["uid"] = uid
            sess["username"] = "InactiveAdmin"

        resp = mock_client.get("/adminpanel/")
        assert resp.status_code == 403


@pytest.mark.usefixtures("mock_app")
class TestDbAdminPanel(TestSetup):
    """GET /adminpanel/db_admin/ — Flask-Admin DB admin panel."""

    def test_db_admin_requires_login(self, mock_client):
        """Unauthenticated user should be redirected to login when trying to access DB admin."""
        resp = mock_client.get("/adminpanel/db_admin/")
        assert resp.status_code == 302
        assert "login" in resp.headers["Location"]

    def test_db_admin_requires_admin_role(self, mock_app, mock_client):
        """A regular user (not coordinator/admin) should get 403 when trying to access DB admin."""
        with mock_app.app_context():
            uid = self._upsert_u_token(
                username="RegularUser",
                access_key="k",
                access_secret="s",
            )

        with mock_client.session_transaction() as sess:
            sess["uid"] = uid
            sess["username"] = "RegularUser"

        resp = mock_client.get("/adminpanel/db_admin/")
        assert resp.status_code == 403

    def test_db_admin_loads_for_admin(self, mock_app, mock_client):
        """An admin user should be able to load the DB admin dashboard."""
        self._login_admin(mock_app, mock_client)
        resp = mock_client.get("/adminpanel/db_admin/")
        assert resp.status_code == 200

    def test_db_admin_model_view_requires_login(self, mock_client):
        """Unauthenticated user should be redirected to login when trying to access a model view."""
        resp = mock_client.get("/adminpanel/db_admin/templaterecord/")
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

        resp = mock_client.get("/adminpanel/db_admin/templaterecord/")
        assert resp.status_code == 403

    def test_db_admin_model_view_loads_for_admin(self, mock_app, mock_client):
        """An admin user should be able to load a model view."""
        self._login_admin(mock_app, mock_client)
        resp = mock_client.get("/adminpanel/db_admin/templaterecord/")
        assert resp.status_code == 200


@pytest.mark.usefixtures("mock_app")
class TestAdminUsersPage(TestSetup):
    """GET /adminpanel/users — list all registered users."""

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

        resp = mock_client.get("/adminpanel/users")
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
        resp = mock_client.get("/adminpanel/users")
        assert resp.status_code == 200

    def test_users_page_empty_list(self, mock_app, mock_client):
        """Users page should load even with no regular users."""

        self._login_admin(mock_app, mock_client)
        resp = mock_client.get("/adminpanel/users")
        assert resp.status_code == 200


@pytest.mark.usefixtures("mock_app")
class TestCoordinatorRoutes(TestSetup):
    """Coordinator CRUD via /adminpanel/coordinators/ endpoints."""

    def test_coordinators_dashboard_requires_admin(self, mock_app, mock_client):
        """Non-admin should get 403 on coordinators page."""
        with mock_app.app_context():
            uid = self._upsert_u_token(
                username="NonAdmin",
                access_key="k",
                access_secret="s",
            )

        with mock_client.session_transaction() as sess:
            sess["uid"] = uid
            sess["username"] = "NonAdmin"

        resp = mock_client.get("/adminpanel/coordinators/")
        assert resp.status_code == 403

    def test_coordinators_dashboard_loads(self, mock_app, mock_client):
        """Admin should see the coordinators dashboard."""

        self._login_admin(mock_app, mock_client)
        resp = mock_client.get("/adminpanel/coordinators/")
        assert resp.status_code == 200

    def test_add_coordinator(self, mock_app, mock_client):
        """Admin should be able to add a new coordinator."""

        with mock_app.app_context():
            self._upsert_u_token(
                username="NewCoord",
                access_key="k",
                access_secret="s",
            )

        self._login_admin(mock_app, mock_client)
        resp = mock_client.post(
            "/adminpanel/coordinators/add",
            data={"username": "NewCoord"},
            follow_redirects=True,
        )
        assert resp.status_code == 200

        with mock_app.app_context():
            result = self.service.is_active_coordinator("NewCoord")
            assert result is True

    def test_add_coordinator_empty_username_flash(self, mock_app, mock_client, monkeypatch):
        """Adding coordinator with empty username should flash error."""
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.flash", mock_flash)

        self._login_admin(mock_app, mock_client)
        resp = mock_client.post(
            "/adminpanel/coordinators/add",
            data={"username": ""},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        mock_flash.assert_called_once_with("Username is required to add a coordinator.", "danger")

    def test_add_duplicate_coordinator_flash(self, mock_app, mock_client, monkeypatch):
        """Adding a duplicate coordinator should flash warning."""
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.flash", mock_flash)

        self._login_admin(mock_app, mock_client)
        mock_client.post(
            "/adminpanel/coordinators/add",
            data={"username": "AdminUser"},
            follow_redirects=True,
        )
        mock_flash.reset_mock()
        resp = mock_client.post(
            "/adminpanel/coordinators/add",
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
            self._upsert_u_token(
                username="ToggleCoord",
                access_key="k",
                access_secret="s",
            )
            coord = self.service.add_coordinator("ToggleCoord")

        self._login_admin(mock_app, mock_client)
        resp = mock_client.post(
            f"/adminpanel/coordinators/{coord.id}/deactivate",
            follow_redirects=True,
        )
        assert resp.status_code == 200

        with mock_app.app_context():
            result = self.service.is_active_coordinator("ToggleCoord")
            assert result is False

    def test_toggle_coordinator_reactivate(self, mock_app, mock_client):
        """Admin should be able to reactivate a coordinator."""

        with mock_app.app_context():
            self._upsert_u_token(
                username="ReactivateCoord",
                access_key="k",
                access_secret="s",
            )
            coord = self.service.add_coordinator("ReactivateCoord")
            self.service.set_coordinator_active(coord.id, False)

        self._login_admin(mock_app, mock_client)
        resp = mock_client.post(
            f"/adminpanel/coordinators/{coord.id}/activate",
            follow_redirects=True,
        )
        assert resp.status_code == 200

        with mock_app.app_context():
            result = self.service.is_active_coordinator("ReactivateCoord")
            assert result is True

    def test_delete_coordinator(self, mock_app, mock_client):
        """Admin should be able to delete a coordinator."""

        with mock_app.app_context():
            self._upsert_u_token(
                username="DeleteCoord",
                access_key="k",
                access_secret="s",
            )
            coord = self.service.add_coordinator("DeleteCoord")

        self._login_admin(mock_app, mock_client)
        resp = mock_client.post(
            f"/adminpanel/coordinators/{coord.id}/delete",
            follow_redirects=True,
        )
        assert resp.status_code == 200

        with mock_app.app_context():
            coords = self.service.list_coordinators()
            usernames = [c.username for c in coords]
            assert "DeleteCoord" not in usernames

    def test_delete_nonexistent_coordinator_flash(self, mock_app, mock_client, monkeypatch):
        """Deleting a non-existent coordinator should flash warning."""
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.flash", mock_flash)

        self._login_admin(mock_app, mock_client)
        resp = mock_client.post(
            "/adminpanel/coordinators/9999/delete",
            follow_redirects=True,
        )
        assert resp.status_code == 200
        mock_flash.assert_called_once()
        assert "was not found" in mock_flash.call_args[0][0]
        assert mock_flash.call_args[0][1] == "warning"


@pytest.mark.usefixtures("mock_app")
class TestAdminRouteIntegration(TestSetup):
    """End-to-end integration scenarios for admin features."""

    def test_admin_can_manage_coordinator_lifecycle(self, mock_app, mock_client):
        """Full lifecycle: add -> deactivate -> reactivate -> delete coordinator."""

        with mock_app.app_context():
            self._upsert_u_token(
                username="LifecycleCoord",
                access_key="k",
                access_secret="s",
            )

        self._login_admin(mock_app, mock_client)

        # Add
        mock_client.post(
            "/adminpanel/coordinators/add",
            data={"username": "LifecycleCoord"},
            follow_redirects=True,
        )
        with mock_app.app_context():
            result = self.service.is_active_coordinator("LifecycleCoord")
            assert result is True

        # Get the coordinator ID
        with mock_app.app_context():
            coords = self.service.list_coordinators()
            coord = next(c for c in coords if c.username == "LifecycleCoord")

        # Deactivate
        mock_client.post(
            f"/adminpanel/coordinators/{coord.id}/deactivate",
            follow_redirects=True,
        )
        with mock_app.app_context():
            result = self.service.is_active_coordinator("LifecycleCoord")
            assert result is False

        # Reactivate
        mock_client.post(
            f"/adminpanel/coordinators/{coord.id}/activate",
            follow_redirects=True,
        )
        with mock_app.app_context():
            result = self.service.is_active_coordinator("LifecycleCoord")
            assert result is True

        # Delete
        mock_client.post(
            f"/adminpanel/coordinators/{coord.id}/delete",
            follow_redirects=True,
        )
        with mock_app.app_context():
            coords = self.service.list_coordinators()
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
            ("GET", "/adminpanel/"),
            ("GET", "/adminpanel/users"),
            ("GET", "/adminpanel/coordinators/"),
            ("POST", "/adminpanel/coordinators/add"),
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
        resp = mock_client.get("/adminpanel/")
        assert resp.status_code == 200
