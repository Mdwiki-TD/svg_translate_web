"""
Unit tests for src/main_app/admin/routes/coordinators.py module.

Classes to test: CoordinatorsRoutes

TODO: write tests
"""

from __future__ import annotations

import pytest

from src.main_app.admin.routes.coordinators import CoordinatorsRoutes  # noqa: F401


@pytest.mark.usefixtures("mock_app")
class TestCoordinatorRoutes:
    def test_dashboard_requires_auth(self, mock_client):
        resp = mock_client.get("/admin/coordinators/")
        assert resp.status_code == 302
