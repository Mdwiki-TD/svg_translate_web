from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from src.main_app.app_routes.main_routes.owid_charts_routes import bp_owid_charts


@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(bp_owid_charts)
    app.secret_key = "test"
    return app
