from unittest.mock import patch

import pytest
from flask import Blueprint, Flask

from src.main_app.public.main_routes.routes import MainRoutes


@pytest.fixture
def app_main_mock():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    bp_main = Blueprint("main", __name__)
    app.register_blueprint(MainRoutes(bp_main).bp)
    app.secret_key = "test"
    return app


@patch("src.main_app.public.main_routes.routes.render_template")
def test_index(mock_render, app_main_mock):
    mock_render.return_value = "rendered"

    with app_main_mock.test_client() as client:
        resp = client.get("/")
        assert resp.data == b"rendered"

        mock_render.assert_called_once()
        args, kwargs = mock_render.call_args
        assert args[0] == "index.html"


def test_favicon(mock_client):

    with mock_client as client:
        resp = client.get("/favicon.ico")
        assert resp.status_code == 200


def test_templates_page_renders_usage_instructions(mock_client):
    """The templates page presents the complete translation workflow to users."""
    response = mock_client.get("/templates/")

    assert response.status_code == 200
    assert b"How to use this page:" in response.data
    assert b"Translate Main File" in response.data
    assert b"Start Job" in response.data
