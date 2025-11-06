"""
Tests for explorer routes.
"""
from pathlib import Path
import tempfile
from unittest.mock import patch

from flask import Blueprint, Flask
import pytest

from src.app.app_routes.explorer.routes import bp_explorer


@pytest.fixture
def app():
    """Create a Flask app instance for testing."""
    app = Flask(__name__, template_folder='../../../../src/templates')
    app.register_blueprint(bp_explorer, url_prefix='/explorer')

    # Create dummy blueprints for url_for calls in templates
    main_bp = Blueprint('main', __name__)
    @main_bp.route('/')
    def index():
        return 'main.index'
    app.register_blueprint(main_bp)

    tasks_bp = Blueprint('tasks', __name__)
    @tasks_bp.route('/tasks')
    def tasks():
        return 'tasks.tasks'
    app.register_blueprint(tasks_bp)

    templates_bp = Blueprint('templates', __name__)
    @templates_bp.route('/templates')
    def main():
        return 'templates.main'
    app.register_blueprint(templates_bp)

    auth_bp = Blueprint('auth', __name__)
    @auth_bp.route('/login')
    def login():
        return 'auth.login'
    app.register_blueprint(auth_bp)

    return app


@pytest.fixture
def client(app):
    """Create a test client for the Flask app."""
    return app.test_client()


@pytest.fixture
def temp_svg_data_dir():
    """Create a temporary directory structure for svg_data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        with patch('src.app.app_routes.explorer.utils.svg_data_path', base_path), \
             patch('src.app.app_routes.explorer.routes.svg_data_path', base_path):
            yield base_path


def test_main(client, temp_svg_data_dir):
    """
    Tests the main explorer page.
    """
    (temp_svg_data_dir / "title1").mkdir()
    response = client.get('/explorer/')
    assert response.status_code == 200
    assert b'title1' in response.data


def test_by_title(client, temp_svg_data_dir):
    """
    Tests the by_title page.
    """
    (temp_svg_data_dir / "title1").mkdir()
    response = client.get('/explorer/title1')
    assert response.status_code == 200
    assert b'title1' in response.data


def test_by_title_downloaded(client, temp_svg_data_dir):
    """
    Tests the by_title_downloaded page.
    """
    (temp_svg_data_dir / "title1" / "files").mkdir(parents=True)
    response = client.get('/explorer/title1/downloads')
    assert response.status_code == 200
    assert b'downloaded Files' in response.data


def test_by_title_translated(client, temp_svg_data_dir):
    """
    Tests the by_title_translated page.
    """
    (temp_svg_data_dir / "title1" / "translated").mkdir(parents=True)
    response = client.get('/explorer/title1/translated')
    assert response.status_code == 200
    assert b'Translated Files' in response.data


def test_by_title_not_translated(client, temp_svg_data_dir):
    """
    Tests the by_title_not_translated page.
    """
    (temp_svg_data_dir / "title1" / "files").mkdir(parents=True)
    (temp_svg_data_dir / "title1" / "translated").mkdir(parents=True)
    response = client.get('/explorer/title1/not_translated')
    assert response.status_code == 200
    assert b'Not Translated Files' in response.data


def test_serve_media(client, temp_svg_data_dir):
    """
    Tests the serve_media route.
    """
    media_dir = temp_svg_data_dir / "title1" / "files"
    media_dir.mkdir(parents=True)
    (media_dir / "test.svg").write_text("<svg></svg>")
    response = client.get('/explorer/media/title1/files/test.svg')
    assert response.status_code == 200
    assert response.data == b'<svg></svg>'


def test_compare(client, temp_svg_data_dir):
    """
    Tests the compare page.
    """
    (temp_svg_data_dir / "title1" / "files").mkdir(parents=True)
    (temp_svg_data_dir / "title1" / "translated").mkdir(parents=True)
    (temp_svg_data_dir / "title1" / "files" / "test.svg").write_text("<svg></svg>")
    (temp_svg_data_dir / "title1" / "translated" / "test.svg").write_text("<svg></svg>")
    response = client.get('/explorer/compare/title1/test.svg')
    assert response.status_code == 200
    assert b'CompareSVGFiles' in response.data.replace(b'\n', b'').replace(b' ', b'')
