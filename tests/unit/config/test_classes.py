from src.main_app.config.classes import (
    CookieConfig,
    DbConfig,
    JobsConfig,
    OAuthConfig,
    OtherConfig,
    Paths,
    SecurityConfig,
    SessionConfig,
    Settings,
)


def test_DbConfig():
    """Test the DbConfig dataclass."""
    db_config = DbConfig(
        db_name="test_db",
        db_host="localhost",
        db_user="user",
        db_password="password",
    )

    assert db_config.db_name == "test_db"
    assert db_config.db_host == "localhost"
    assert db_config.db_user == "user"
    assert db_config.db_password == "password"


def test_Paths():
    """Test the Paths dataclass."""
    paths = Paths(
        svg_data="/svg/data",
        svg_data_thumb="/svg/thumb",
        log_dir="/logs",
        fix_nested_data="/fix/nested",
        svg_jobs_path="/jobs",
        main_files_path="/main_files",
        crop_main_files_path="/crop_main_files",
    )

    assert paths.svg_data == "/svg/data"
    assert paths.svg_data_thumb == "/svg/thumb"
    assert paths.log_dir == "/logs"
    assert paths.fix_nested_data == "/fix/nested"
    assert paths.svg_jobs_path == "/jobs"
    assert paths.main_files_path == "/main_files"
    assert paths.crop_main_files_path == "/crop_main_files"


def test_CookieConfig():
    """Test the CookieConfig dataclass."""
    cookie_config = CookieConfig(name="test_cookie", max_age=3600, secure=True, httponly=True, samesite="Lax")

    assert cookie_config.name == "test_cookie"
    assert cookie_config.max_age == 3600
    assert cookie_config.secure is True
    assert cookie_config.httponly is True
    assert cookie_config.samesite == "Lax"


def test_OAuthConfig():
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


def test_Settings():
    """Test the Settings dataclass."""
    # Create a minimal settings object for testing
    db_config = DbConfig("test", "localhost", "user", "pass")
    cookie_config = CookieConfig("test", 3600, True, True, "Lax")
    paths = Paths("/svg", "/thumb", "/logs", "/fix", "/jobs", "/main_files", "/crop_main_files")

    jobs_config = JobsConfig(
        dev_limit=0,
        disable_uploads="",
        upload_host="upload.example.com",
    )

    security_config = SecurityConfig(
        secret_key="secret",
        max_content_length=100 * 1024 * 1024,
        max_form_memory_size=16 * 1024 * 1024,
        max_form_parts=1000,
        secret_key_fallbacks=(),
    )

    sessions = SessionConfig(
        state_key="state",
        request_token_key="request",
    )

    other_config = OtherConfig(
        user_agent="user_agent",
        csrf_time_limit=3600,
    )

    settings = Settings(
        database_data=db_config,
        cookie=cookie_config,
        sessions=sessions,
        oauth=None,
        paths=paths,
        jobs=jobs_config,
        security=security_config,
        other=other_config,
    )

    assert settings.jobs.upload_host == "upload.example.com"
    assert settings.database_data.db_host == "localhost"
    assert settings.database_data.db_name == "test"
    assert settings.cookie.name == "test"
    assert settings.paths.svg_data == "/svg"
    assert settings.jobs.dev_limit == 0
    assert settings.security.max_content_length == 100 * 1024 * 1024
    assert settings.other.csrf_time_limit == 3600
