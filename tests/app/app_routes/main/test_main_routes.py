from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from src.main_app.app_routes.main.routes import bp_main


@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(bp_main)
    app.secret_key = "test"
    return app


@patch("src.main_app.app_routes.main.routes.render_template")
@patch("src.main_app.app_routes.main.routes.current_user")
def test_index(mock_current_user, mock_render, app):
    mock_current_user.return_value = MagicMock(username="user")
    mock_render.return_value = "rendered"

    with app.test_client() as client:
        resp = client.get("/")
        assert resp.data == b"rendered"

        mock_render.assert_called_once()
        args, kwargs = mock_render.call_args
        assert args[0] == "index.html"
        assert kwargs["current_user"] == mock_current_user.return_value


@patch("src.main_app.app_routes.main.routes.send_from_directory")
def test_favicon(mock_send, app):
    mock_send.return_value = "icon"

    with app.test_client() as client:
        resp = client.get("/favicon.ico")
        assert resp.data == b"icon"

        mock_send.assert_called_once_with("static", "favicon.ico", mimetype="image/x-icon")
