"""
Unit tests for src/main_app/app_routes/admin_routes/coordinators.py module.

Classes to test: CoordinatorsRoutes

TODO: write tests
"""

from __future__ import annotations

import pytest

from src.main_app.app_routes.admin_routes.coordinators import CoordinatorsRoutes  # noqa: F401


@pytest.mark.usefixtures("app")
class TestCoordinatorRoutes:
    def test_dashboard_requires_auth(self, mock_client):
        resp = mock_client.get("/admin/coordinators/")
        assert resp.status_code == 302
