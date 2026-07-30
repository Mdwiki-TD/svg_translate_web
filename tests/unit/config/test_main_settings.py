import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.main_app.config.classes import (
    DbConfig,
    OAuthConfig,
    Paths,
    Settings,
)
from src.main_app.config.main_settings import (
    _env_bool,
    _env_int,
    _get_paths,
    _load_database_config,
    _load_oauth_config,
    get_settings,
)


@patch.dict(
    os.environ,
    {
        "TOOL_TOOLSDB_DBNAME": "test_db",
        "TOOL_TOOLSDB_HOST": "test_host",
        "TOOL_TOOLSDB_USER": "test_user",
        "TOOL_TOOLSDB_PASSWORD": "test_pass",
    },
    clear=True,
)
@patch("os.path.exists")
def test_load_database_config(mock_exists):
    """Test _load_database_config function."""
    mock_exists.return_value = True
    result = _load_database_config()

    assert isinstance(result, DbConfig)
    assert result.db_name == "test_db"
    assert result.db_host == "test_host"
    assert result.db_user == "test_user"
    assert result.db_password == "test_pass"


def test_get_paths(tmp_path):
    """Test _get_paths function."""
    main_dir = str(tmp_path / "main")
    with patch.dict(os.environ, {"MAIN_DIR": main_dir}):
        result = _get_paths()

        assert isinstance(result, Paths)
        assert Path(result.log_dir) == Path(f"{main_dir}/logs")


def test_env_bool():
    """Test _env_bool function."""
    # Test with various truthy values
    with patch.dict(os.environ, {"TEST_BOOL_TRUE": "1"}):
        assert _env_bool("TEST_BOOL_TRUE") is True

    with patch.dict(os.environ, {"TEST_BOOL_TRUE": "true"}):
        assert _env_bool("TEST_BOOL_TRUE") is True

    with patch.dict(os.environ, {"TEST_BOOL_TRUE": "True"}):
        assert _env_bool("TEST_BOOL_TRUE") is True

    with patch.dict(os.environ, {"TEST_BOOL_TRUE": "yes"}):
        assert _env_bool("TEST_BOOL_TRUE") is True

    with patch.dict(os.environ, {"TEST_BOOL_TRUE": "YES"}):
        assert _env_bool("TEST_BOOL_TRUE") is True

    with patch.dict(os.environ, {"TEST_BOOL_TRUE": "on"}):
        assert _env_bool("TEST_BOOL_TRUE") is True

    with patch.dict(os.environ, {"TEST_BOOL_FALSE": "false"}):
        assert _env_bool("TEST_BOOL_FALSE") is False

    # Test missing variable (should return default)
    with patch.dict(os.environ, {}, clear=True):
        assert _env_bool("TEST_BOOL_MISSING", default=True) is True

    assert _env_bool("NONEXISTENT_VAR", default=False) is False


def test_env_int():
    """Test _env_int function."""
    with patch.dict(os.environ, {"TEST_INT": "42"}):
        assert _env_int("TEST_INT", default=0) == 42
        assert isinstance(_env_int("TEST_INT", default=0), int)

    assert _env_int("NONEXISTENT_VAR", default=100) == 100

    with patch.dict(os.environ, {"TEST_INVALID": "not_a_number"}):
        with pytest.raises(ValueError):
            _env_int("TEST_INVALID", default=0)


@patch.dict(
    os.environ,
    {
        "OAUTH_MWURI": "https://example.com",
        "OAUTH_CONSUMER_KEY": "key",
        "OAUTH_CONSUMER_SECRET": "secret",
        "USER_AGENT": "test-agent",
        "WIKI_DOMAIN": "upload.example.com",
    },
)
def test_load_oauth_config():
    """Test _load_oauth_config function."""
    result = _load_oauth_config()

    assert isinstance(result, OAuthConfig)
    assert result.mw_uri == "https://example.com"
    assert result.consumer_key == "key"
    assert result.consumer_secret == "secret"


def test_get_settings(tmp_path):
    """Test get_settings function."""
    # Clear the LRU cache to ensure fresh call
    get_settings.cache_clear()

    with patch.dict(
        os.environ,
        {
            "FLASK_SECRET_KEY": "test-secret-key",
            "SESSION_COOKIE_SECURE": "true",
            "SESSION_COOKIE_HTTPONLY": "true",
            "SESSION_COOKIE_SAMESITE": "Strict",
            "STATE_SESSION_KEY": "test-state",
            "REQUEST_TOKEN_SESSION_KEY": "test-request",
            "AUTH_COOKIE_NAME": "test-cookie",
            "AUTH_COOKIE_MAX_AGE": "7200",
            "MAIN_DIR": str(tmp_path / "test-data"),
        },
    ):
        settings = get_settings()

        assert isinstance(settings, Settings)
        assert settings.security.secret_key == "test-secret-key"
        assert settings.cookie.name == "test-cookie"
        assert settings.cookie.max_age == 7200
        assert settings.sessions.state_key == "test-state"
        assert settings.sessions.request_token_key == "test-request"

    # Clean up cache
    get_settings.cache_clear()


def test_get_settings_missing_secret_key():
    """Test get_settings raises error when secret key is missing."""
    with patch.dict(os.environ, {}, clear=True):
        get_settings.cache_clear()
        with pytest.raises(RuntimeError, match="FLASK_SECRET_KEY environment variable is required"):
            get_settings()

    # Clean up cache
    get_settings.cache_clear()


@patch.dict(os.environ, {"TOOL_TOOLSDB_DBNAME": "", "TOOL_TOOLSDB_HOST": ""}, clear=True)
def test_load_database_config_empty_values():
    """Test _load_database_config with empty environment variables."""
    result = _load_database_config()
    assert result.db_name == ""
    assert result.db_host == ""
    assert result.db_user is None
    assert result.db_password is None


def test_env_bool_with_whitespace():
    """Test _env_bool with whitespace in values."""
    with patch.dict(os.environ, {"TEST_BOOL": "  1  "}):
        assert _env_bool("TEST_BOOL") is True

    with patch.dict(os.environ, {"TEST_BOOL": "  true  "}):
        assert _env_bool("TEST_BOOL") is True


def test_env_int_edge_cases():
    """Test _env_int with edge case values."""
    # Test zero
    with patch.dict(os.environ, {"TEST_INT": "0"}):
        assert _env_int("TEST_INT", default=10) == 0

    # Test negative
    with patch.dict(os.environ, {"TEST_INT": "-5"}):
        assert _env_int("TEST_INT", default=10) == -5

    # Test large number
    with patch.dict(os.environ, {"TEST_INT": "999999"}):
        assert _env_int("TEST_INT", default=0) == 999999


@patch.dict(
    os.environ, {"OAUTH_MWURI": "https://example.com", "OAUTH_CONSUMER_KEY": "key", "OAUTH_CONSUMER_SECRET": "secret"}
)
def test_load_oauth_config_with_defaults():
    """Test _load_oauth_config uses default values when optional vars missing."""
    result = _load_oauth_config()

    assert result is not None
    assert result.mw_uri == "https://example.com"
    assert result.consumer_key == "key"
    assert result.consumer_secret == "secret"


class TestConfig:
    def test_get_settings_missing_oauth_encryption_key(self, tmp_path):
        """Test get_settings raises error when OAuth is enabled but encryption key is missing."""
        get_settings.cache_clear()
        with patch.dict(
            os.environ,
            {
                "FLASK_SECRET_KEY": "test-secret-key",
                "OAUTH_MWURI": "https://example.com",
                "OAUTH_CONSUMER_KEY": "key",
                "OAUTH_CONSUMER_SECRET": "secret",
                "MAIN_DIR": str(tmp_path / "test-data"),
            },
            clear=True,
        ):
            with pytest.raises(RuntimeError, match="OAUTH_ENCRYPTION_KEY environment variable is required"):
                get_settings()
        get_settings.cache_clear()

    def test_get_settings_missing_oauth_config(self, tmp_path):
        """Test get_settings raises error when OAuth is enabled but OAuth config is incomplete."""
        get_settings.cache_clear()
        with patch.dict(
            os.environ,
            {
                "FLASK_SECRET_KEY": "test-secret-key",
                "OAUTH_ENCRYPTION_KEY": "test-key",
                "MAIN_DIR": str(tmp_path / "test-data"),
            },
            clear=True,
        ):
            with pytest.raises(RuntimeError, match="MediaWiki OAuth configuration is incomplete"):
                get_settings()
        get_settings.cache_clear()
