"""
Unit tests for src/main_app/adminpanel/routes/coordinators.py module.
"""

from __future__ import annotations

from unittest.mock import MagicMock, Mock

import pytest

from src.main_app.admin.routes.coordinators import CoordinatorsFuncs
from src.main_app.db.exceptions import DuplicateUserError, UserNotFoundError


@pytest.mark.usefixtures("mock_app")
class TestCoordinatorRoutes:
    def test_dashboard_requires_auth(self, mock_client):
        resp = mock_client.get("/adminpanel/coordinators/")
        assert resp.status_code == 302


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.service = CoordinatorsFuncs()


class TestCoordinatorsDashboard(TestSetup):
    def test_renders_with_coordinators(self, monkeypatch):
        mock_coord = MagicMock()
        mock_coord.is_active = True
        monkeypatch.setattr(self.service.service, "list_coordinators", lambda: [mock_coord])
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.render_template", lambda t, **c: c)
        result = self.service.dashboard()
        assert result["total_coordinators"] == 1
        assert result["total_active_coordinators"] == 1

    def test_renders_with_empty_list(self, monkeypatch):
        monkeypatch.setattr(self.service.service, "list_coordinators", list)
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.render_template", lambda t, **c: c)
        result = self.service.dashboard()
        assert result["total_coordinators"] == 0

    def test_handles_exception(self, monkeypatch):
        monkeypatch.setattr(
            self.service.service, "list_coordinators", Mock(side_effect=Exception("DB error"))
        )
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.flash", Mock())
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.render_template", lambda t, **c: c)
        result = self.service.dashboard()
        assert result["total_coordinators"] == 0


class TestAddCoordinator(TestSetup):
    def test_missing_username(self, monkeypatch):
        mock_request = Mock()
        mock_request.form.get.return_value = ""
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.request", mock_request)
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.flash", Mock())
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.url_for", lambda x: f"/{x}")
        result = self.service.add()
        assert "redirect" in result

    def test_user_not_found(self, monkeypatch):
        mock_request = Mock()
        mock_request.form.get.return_value = "unknown_user"
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.request", mock_request)
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.url_for", lambda x: f"/{x}")
        mock_add = Mock(side_effect=UserNotFoundError("User does not exist"))
        monkeypatch.setattr(self.service.service, "add_coordinator", mock_add)
        self.service.add()
        mock_flash.assert_called()

    def test_duplicate_user(self, monkeypatch):
        mock_request = Mock()
        mock_request.form.get.return_value = "existing_user"
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.request", mock_request)
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.url_for", lambda x: f"/{x}")
        mock_add = Mock(side_effect=DuplicateUserError("Already exists"))
        monkeypatch.setattr(self.service.service, "add_coordinator", mock_add)
        self.service.add()
        mock_flash.assert_called()

    def test_success(self, monkeypatch):
        mock_request = Mock()
        mock_request.form.get.return_value = "new_user"
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.request", mock_request)
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.url_for", lambda x: f"/{x}")
        mock_record = MagicMock()
        mock_record.username = "new_user"
        mock_add = Mock(return_value=mock_record)
        monkeypatch.setattr(self.service.service, "add_coordinator", mock_add)
        self.service.add()
        mock_flash.assert_called_with("Coordinator 'new_user' added.", "success")


class TestSetRecordActiveStatus(TestSetup):
    def test_activate_success(self, monkeypatch):
        mock_record = MagicMock()
        mock_record.is_active = True
        mock_record.username = "testuser"
        monkeypatch.setattr(self.service.service, "set_coordinator_active", lambda i, a: mock_record)
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.url_for", lambda x: f"/{x}")
        self.service.activate(1)
        mock_flash.assert_called_with("Coordinator 'testuser' activated.", "success")

    def test_deactivate_success(self, monkeypatch):
        mock_record = MagicMock()
        mock_record.is_active = False
        mock_record.username = "testuser"
        monkeypatch.setattr(self.service.service, "set_coordinator_active", lambda i, a: mock_record)
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.url_for", lambda x: f"/{x}")
        self.service.deactivate(1)
        mock_flash.assert_called_with("Coordinator 'testuser' deactivated.", "success")

    def test_not_found(self, monkeypatch):
        monkeypatch.setattr(self.service.service, "set_coordinator_active", lambda i, a: None)
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.url_for", lambda x: f"/{x}")
        self.service.activate(999)
        mock_flash.assert_called()


class TestDeleteCoordinator(TestSetup):
    def test_success(self, monkeypatch):
        mock_record = MagicMock()
        mock_record.id = 1
        monkeypatch.setattr(self.service.service, "get_coordinator_by_id", lambda i: mock_record)
        monkeypatch.setattr(self.service.service, "delete_coordinator", lambda i: None)
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.url_for", lambda x: f"/{x}")
        self.service.delete(1)
        mock_flash.assert_called_with("Coordinator '1' removed.", "success")

    def test_not_found(self, monkeypatch):
        monkeypatch.setattr(
            self.service.service, "get_coordinator_by_id", Mock(side_effect=LookupError("not found"))
        )
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.url_for", lambda x: f"/{x}")
        self.service.delete(999)
        mock_flash.assert_called()
