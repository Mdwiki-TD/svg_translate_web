"""Unit tests for src/main_app/core/cookies.py module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from src.main_app.shared.core.cookies.cookie_header_client import CookieHeaderClient


class TestCookieHeaderClientLite:
    def test_class_is_subclass_of_flask_client(self):
        from flask.testing import FlaskClient

        assert issubclass(CookieHeaderClient, FlaskClient)

    def test_open_with_no_headers(self, mock_app):
        """Calling open with no headers should not crash."""
        with mock_app.test_client() as client:
            resp = client.get("/")
            assert resp.status_code == 200

    def test_open_with_dict_headers_no_cookie(self, mock_app):
        """Dict headers without Cookie key should pass through."""
        with mock_app.test_client() as client:
            resp = client.get("/", headers={"X-Custom": "value"})
            assert resp.status_code == 200

    def test_open_with_list_headers_no_cookie(self, mock_app):
        """List-of-tuple headers without cookie should pass through."""
        with mock_app.test_client() as client:
            resp = client.get("/", headers=[("X-Custom", "value")])
            assert resp.status_code == 200


class TestCookieHeaderClient:
    @pytest.fixture
    def app_c_mock(self) -> Flask:
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"
        app.test_client_class = CookieHeaderClient
        return app

    @pytest.fixture
    def mock_c_client(self, app_c_mock: Flask) -> CookieHeaderClient:
        return app_c_mock.test_client()

    def test_open_with_dict_headers_and_cookie(self, mock_c_client: CookieHeaderClient) -> None:
        response = mock_c_client.get("/", headers={"Cookie": "session=abc123"})
        assert response.status_code == 404

    def test_open_with_tuple_headers_and_cookie(self, mock_c_client: CookieHeaderClient) -> None:
        response = mock_c_client.get("/", headers=[("Cookie", "session=xyz789")])
        assert response.status_code == 404

    def test_open_without_cookie_header(self, mock_c_client: CookieHeaderClient) -> None:
        response = mock_c_client.get("/", headers={"Accept": "text/html"})
        assert response.status_code == 404

    def test_open_with_empty_headers(self, mock_c_client: CookieHeaderClient) -> None:
        response = mock_c_client.get("/", headers={})
        assert response.status_code == 404

    def test_open_with_none_headers(self, mock_c_client: CookieHeaderClient) -> None:
        response = mock_c_client.get("/")
        assert response.status_code == 404

    def test_open_with_case_insensitive_cookie(self, mock_c_client: CookieHeaderClient) -> None:
        response = mock_c_client.get("/", headers={"cookie": "session=lower"})
        assert response.status_code == 404

    def test_open_with_multiple_cookies(self, mock_c_client: CookieHeaderClient) -> None:
        response = mock_c_client.get("/", headers={"Cookie": "a=1; b=2; c=3"})
        assert response.status_code == 404

    def test_open_with_cookie_and_other_headers(self, mock_c_client: CookieHeaderClient) -> None:
        response = mock_c_client.get(
            "/",
            headers={
                "Cookie": "session=test",
                "Accept": "application/json",
                "X-Custom": "value",
            },
        )
        assert response.status_code == 404

    def test_open_strips_cookie_from_headers(self, app_c_mock: Flask) -> None:
        client = app_c_mock.test_client()

        with patch.object(app_c_mock.test_client_class.__bases__[0], "open") as mock_super_open:  # type: ignore
            mock_response = MagicMock()
            mock_super_open.return_value = mock_response

            client.open("/", headers={"Cookie": "session=test", "Accept": "text/html"})

            mock_super_open.assert_called_once()
            call_kwargs = mock_super_open.call_args.kwargs
            assert "headers" in call_kwargs
            passed_headers = call_kwargs["headers"]
            assert isinstance(passed_headers, dict)
            assert "Cookie" not in passed_headers
            assert "cookie" not in passed_headers
            assert passed_headers.get("Accept") == "text/html"

    def test_open_handles_tuple_cookie_header(self, app_c_mock: Flask) -> None:
        client = app_c_mock.test_client()

        with patch.object(app_c_mock.test_client_class.__bases__[0], "open") as mock_super_open:  # type: ignore
            mock_response = MagicMock()
            mock_super_open.return_value = mock_response

            client.open("/", headers=[("Cookie", "session=xyz"), ("Accept", "text/html")])

            mock_super_open.assert_called_once()
            call_kwargs = mock_super_open.call_args.kwargs
            assert "headers" in call_kwargs
            passed_headers = call_kwargs["headers"]
            assert ("Cookie", "session=xyz") not in passed_headers
            assert ("Accept", "text/html") in passed_headers

    def test_open_without_cookie_preserves_headers(self, app_c_mock: Flask) -> None:
        client = app_c_mock.test_client()

        with patch.object(app_c_mock.test_client_class.__bases__[0], "open") as mock_super_open:  # type: ignore
            mock_response = MagicMock()
            mock_super_open.return_value = mock_response

            client.open("/", headers={"Accept": "text/html"})

            mock_super_open.assert_called_once()
            call_kwargs = mock_super_open.call_args.kwargs
            assert "headers" in call_kwargs
            assert call_kwargs["headers"] == {"Accept": "text/html"}

    def test_cookie_header_client_subclass(self) -> None:
        assert issubclass(CookieHeaderClient, object)
