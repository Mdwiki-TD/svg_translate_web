"""
Unit tests for src/main_app/app_routes/admin_routes/coordinators.py module.

Classes to test: CoordinatorsRoutes

TODO: write tests
"""

from __future__ import annotations

from flask import Flask
from flask.testing import FlaskClient
import pytest

from src.main_app.app_routes.admin_routes.coordinators import CoordinatorsRoutes  # noqa: F401


@pytest.fixture
def mk_client(mock_app: Flask) -> FlaskClient:
    """Fresh test client per test."""

    return mock_app.test_client()



@pytest.mark.usefixtures("mock_app")
class TestCoordinatorRoutes:
    def test_dashboard_requires_auth(self, mk_client):
        resp = mk_client.get("/admin/coordinators/")
        assert resp.status_code == 302
