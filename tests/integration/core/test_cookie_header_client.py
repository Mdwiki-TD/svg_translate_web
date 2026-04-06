"""Tests for CookieHeaderClient behavior."""

from flask import Flask, request

from src.main_app.core.cookies import CookieHeaderClient


def test_cookie_header_client_sets_cookie_from_header():
    app_mock = Flask(__name__)
    app_mock.url_map.strict_slashes = False
    app_mock.test_client_class = CookieHeaderClient
    app_mock.config.update(TESTING=True, SERVER_NAME="localhost")

    @app_mock.get("/echo")
    def echo():
        return request.cookies.get("foo", "")  # pragma: no cover - trivial

    with app_mock.test_client() as client:
        resp = client.get("/echo", headers={"Cookie": "foo=bar"})
        assert resp.status_code == 200
        assert resp.data.decode() == "bar"
