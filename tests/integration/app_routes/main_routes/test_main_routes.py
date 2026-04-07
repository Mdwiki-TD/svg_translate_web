from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from src.main_app.app_routes.main_routes.routes import bp_main


@pytest.fixture
def app_mock():
    app = Flask(__name__)
    app.register_blueprint(bp_main)
    app.secret_key = "test"
    return app


@patch("src.main_app.app_routes.main_routes.routes.render_template")
def test_index(mock_render, app_mock):
    mock_render.return_value = "rendered"

    with app_mock.test_client() as client:
        resp = client.get("/")
        assert resp.data == b"rendered"

        mock_render.assert_called_once()
        args, kwargs = mock_render.call_args
        assert args[0] == "index.html"
        assert kwargs["form"] == {}
        assert kwargs["set_titles_limit"] == False


@patch("src.main_app.app_routes.main_routes.routes.send_from_directory")
def test_favicon(mock_send, app_mock):
    mock_send.return_value = "icon"

    with app_mock.test_client() as client:
        resp = client.get("/favicon.ico")
        assert resp.data == b"icon"

        mock_send.assert_called_once_with("static", "favicon.ico", mimetype="image/x-icon")
