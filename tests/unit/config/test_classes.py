"""Unit tests for src/main_app/config/classes.py module."""

from __future__ import annotations

from pathlib import Path

from src.main_app.config.classes import (
    CookieConfig,
    JobsConfig,
    OAuthConfig,
    OtherConfig,
    Paths,
    SecurityConfig,
    SessionConfig,
    Settings,
)


def test_paths():
    """Test the Paths dataclass."""
    paths = Paths(
        flask_data_dir=Path("/"),
        log_dir=Path("/logs"),
        jobs_path=Path("/jobs"),
        admin_jobs_path=Path("/jobs"),
    )

    assert paths.log_dir == Path("/logs")
    assert paths.jobs_path == Path("/jobs")


def test_cookieconfig():
    """Test the CookieConfig dataclass."""
    cookie_config = CookieConfig(name="test_cookie", max_age=3600, secure=True, httponly=True, samesite="Lax")

    assert cookie_config.name == "test_cookie"
    assert cookie_config.max_age == 3600
    assert cookie_config.secure is True
    assert cookie_config.httponly is True
    assert cookie_config.samesite == "Lax"


def test_oauthconfig():
    """Test the OAuthConfig dataclass."""
    oauth_config = OAuthConfig(
        mw_uri="https://example.com",
        consumer_key="key",
        consumer_secret="secret",
        encryption_key="encryption_key",
    )

    assert oauth_config.mw_uri == "https://example.com"
    assert oauth_config.consumer_key == "key"
    assert oauth_config.consumer_secret == "secret"


def test_settings():
    """Test the Settings dataclass."""
    # Create a minimal settings object for testing
    cookie_config = CookieConfig("test", 3600, True, True, "Lax")
    paths = Paths(
        flask_data_dir=Path("/"),
        log_dir=Path("/logs"),
        jobs_path=Path("/jobs"),
        admin_jobs_path=Path("/jobs"),
    )

    jobs_config = JobsConfig(
        jobs_max_workers=10,
        jobs_log_lines=10,
    )

    security_config = SecurityConfig(
        salt="svg-translate",
        secret_key="secret",
        max_content_length=100 * 1024 * 1024,
        max_form_memory_size=16 * 1024 * 1024,
        max_form_parts=1000,
        secret_key_fallbacks=(),
    )

    sessions = SessionConfig(
        state_key="state",
        request_token_key="request",
        request_secret_key="request_secret",
    )

    other_config = OtherConfig(
        user_agent="user_agent",
        csrf_time_limit=3600,
        static_server="static_server",
        wiki_domain="upload.example.com",
        tool_title="tool_title",
    )

    app_settings = Settings(
        cookie=cookie_config,
        sessions=sessions,
        oauth=OAuthConfig.load(),
        paths=paths,
        jobs=jobs_config,
        security=security_config,
        other=other_config,
    )

    assert app_settings.other.wiki_domain == "upload.example.com"
    assert app_settings.cookie.name == "test"
    assert app_settings.security.max_content_length == 100 * 1024 * 1024
    assert app_settings.other.csrf_time_limit == 3600
