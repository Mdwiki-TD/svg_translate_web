"""
Unit tests for src/main_app/adminpanel/routes/coordinators.py module.
"""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock, Mock

import pytest

from src.main_app.admin.routes.coordinators import CoordinatorsFuncs
from src.main_app.db.exceptions import DuplicateRecordError, UserNotFoundError


@pytest.mark.usefixtures("mock_app")
class TestCoordinatorRoutes:
    def test_dashboard_requires_auth(self, mock_client):
        resp = mock_client.get("/adminpanel/coordinators/")
        assert resp.status_code == 302


@dataclass
class MockAdminServiceMethods:
    """Bundle of every mock patched onto CoordinatorsFuncs.admin_service()."""

    list_coordinators: MagicMock
    add_coordinator: MagicMock
    set_coordinator_active: MagicMock
    get_coordinator_by_id: MagicMock
    delete: MagicMock


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        self.service = CoordinatorsFuncs()

    @pytest.fixture(autouse=True)
    def setup_mocks(self, monkeypatch):
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.render_template", lambda t, **c: c)
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.url_for", lambda x: f"/{x}")

        self.mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.coordinators.flash", self.mock_flash)

        self.mock_service = MockAdminServiceMethods(
            list_coordinators=MagicMock(return_value=[]),
            add_coordinator=MagicMock(),
            set_coordinator_active=MagicMock(),
            get_coordinator_by_id=MagicMock(),
            delete=MagicMock(),
        )
        monkeypatch.setattr(self.service.admin_service, "list_coordinators", self.mock_service.list_coordinators)
        monkeypatch.setattr(self.service.admin_service, "add_coordinator", self.mock_service.add_coordinator)
        monkeypatch.setattr(
            self.service.admin_service, "set_coordinator_active", self.mock_service.set_coordinator_active
        )
        monkeypatch.setattr(
            self.service.admin_service, "get_coordinator_by_id", self.mock_service.get_coordinator_by_id
        )
        monkeypatch.setattr(self.service.admin_service, "delete", self.mock_service.delete)


class TestCoordinatorsDashboard(TestSetup):
    def test_renders_with_coordinators(self):
        mock_coord = MagicMock()
        mock_coord.is_active = True
        self.mock_service.list_coordinators.return_value = [mock_coord]

        result = self.service.dashboard()
        assert result["total_coordinators"] == 1
        assert result["total_active_coordinators"] == 1

    def test_renders_with_empty_list(self):
        self.mock_service.list_coordinators.return_value = []

        result = self.service.dashboard()
        assert result["total_coordinators"] == 0

    def test_handles_exception(self):
        self.mock_service.list_coordinators.side_effect = Exception("DB error")

        result = self.service.dashboard()
        assert result["total_coordinators"] == 0


class TestAddCoordinator(TestSetup):
    @pytest.fixture
    def make_mock_request(self, monkeypatch):
        def _factory(username: str) -> Mock:
            mock_request = Mock()
            mock_request.form.get.return_value = username
            monkeypatch.setattr("src.main_app.admin.routes.coordinators.request", mock_request)
            return mock_request

        return _factory

    def test_missing_username(self, make_mock_request):
        make_mock_request("")

        result = self.service.add()
        assert "redirect" in result

    def test_user_not_found(self, make_mock_request):
        make_mock_request("unknown_user")
        self.mock_service.add_coordinator.side_effect = UserNotFoundError("User does not exist")

        self.service.add()
        self.mock_flash.assert_called()

    def test_duplicate_user(self, make_mock_request):
        make_mock_request("existing_user")
        self.mock_service.add_coordinator.side_effect = DuplicateRecordError("Already exists")

        self.service.add()
        self.mock_flash.assert_called()

    def test_success(self, make_mock_request):
        make_mock_request("new_user")
        mock_record = MagicMock()
        mock_record.username = "new_user"
        self.mock_service.add_coordinator.return_value = mock_record

        self.service.add()
        self.mock_flash.assert_called_with("Coordinator 'new_user' added.", "success")


class TestSetRecordActiveStatus(TestSetup):
    def test_activate_success(self):
        mock_record = MagicMock()
        mock_record.is_active = True
        mock_record.username = "testuser"
        self.mock_service.set_coordinator_active.return_value = mock_record

        self.service.activate(1)
        self.mock_flash.assert_called_with("Coordinator 'testuser' activated.", "success")

    def test_deactivate_success(self):
        mock_record = MagicMock()
        mock_record.is_active = False
        mock_record.username = "testuser"
        self.mock_service.set_coordinator_active.return_value = mock_record

        self.service.deactivate(1)
        self.mock_flash.assert_called_with("Coordinator 'testuser' deactivated.", "success")

    def test_not_found(self):
        self.mock_service.set_coordinator_active.return_value = None

        self.service.activate(999)
        self.mock_flash.assert_called()


class TestDeleteCoordinator(TestSetup):
    def test_success(self):
        mock_record = MagicMock()
        mock_record.id = 1
        self.mock_service.get_coordinator_by_id.return_value = mock_record
        self.mock_service.delete.return_value = None

        self.service.delete(1)
        self.mock_flash.assert_called_with("Coordinator '1' removed.", "success")

    def test_not_found(self):
        self.mock_service.get_coordinator_by_id.side_effect = LookupError("not found")

        self.service.delete(999)
        self.mock_flash.assert_called()
