"""Unit tests for src/main_app/services/auth/flow.py module."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from flask import Blueprint, Flask, g, session
from mwoauth import AccessToken
from src.main_app.services.auth.auth_exceptions import (
    OAuthCallbackError,
    OAuthIdentityError,
)
from src.main_app.services.auth.flow import AuthFlowService


@pytest.fixture
def app() -> Flask:
    """Create a minimal Flask application for request/session/g contexts."""
    flask_app = Flask(__name__)
    flask_app.config["SECRET_KEY"] = "test-secret-key"
    flask_app.config["SERVER_NAME"] = "example.test"
    flask_app.config["APPLICATION_ROOT"] = "/"
    flask_app.config["PREFERRED_URL_SCHEME"] = "https"

    bp_auth = Blueprint("auth", __name__, url_prefix="/auth")

    @bp_auth.route("/callback")
    def callback() -> str:
        return "callback"

    flask_app.register_blueprint(bp_auth)
    return flask_app


@pytest.fixture
def mock_settings() -> SimpleNamespace:
    """Provide deterministic settings for AuthFlowService."""
    return SimpleNamespace(
        oauth=SimpleNamespace(
            consumer_key="consumer-key",
            consumer_secret="consumer-secret",
            mw_uri="https://meta.wikimedia.org/w/index.php",
        ),
        other=SimpleNamespace(
            user_agent="TestUserAgent/1.0",
        ),
        sessions=SimpleNamespace(
            request_secret_key="oauth_request_secret",
            request_token_key="oauth_token",
            state_key="oauth_state_nonce",
        ),
        cookie=SimpleNamespace(
            name="auth_token",
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=3600,
        ),
    )


@pytest.fixture
def mocks() -> dict[str, MagicMock]:
    """Create mocked dependencies for AuthFlowService."""
    oauth_service = MagicMock()
    token_manager = MagicMock()
    user_svc = MagicMock()
    token_signer = MagicMock()

    # Default happy-path behaviors
    oauth_service.create_authorization_url.return_value = (
        "https://meta.wikimedia.org/oauth/authorize?oauth_token=req_tok",
        "req_tok",
        "req_sec",
    )
    oauth_service.fetch_access_token.return_value = AccessToken(
        key="acc_key",
        secret="acc_secret",
    )
    oauth_service.identify.return_value = {"username": "WikiEditor"}

    token_signer.sign_state_token.side_effect = lambda nonce: f"signed:{nonce}"
    token_signer.verify_state_token.side_effect = lambda token: token.removeprefix("signed:")
    token_signer.sign_user_id.side_effect = lambda uid: f"signed_uid:{uid}"
    token_signer.extract_user_id.return_value = 42

    user_svc.ensure_exists.return_value = SimpleNamespace(user_id=42, username="WikiEditor")
    token_manager.save_token.return_value = SimpleNamespace(id=1)
    token_manager.get_authenticated_user.return_value = SimpleNamespace(user_id=42, username="WikiEditor")

    return {
        "oauth_service": oauth_service,
        "token_manager": token_manager,
        "user_svc": user_svc,
        "token_signer": token_signer,
    }


@pytest.fixture
def service(
    mock_settings: SimpleNamespace,
    mocks: dict[str, MagicMock],
) -> AuthFlowService:
    """Instantiate AuthFlowService with mocked collaborators."""
    return AuthFlowService(
        app_settings=mock_settings,  # type: ignore[arg-type]
        oauth_service=mocks["oauth_service"],
        token_manager=mocks["token_manager"],
        user_svc=mocks["user_svc"],
        token_signer=mocks["token_signer"],
    )


# ----------------------------------------------------------------------
# Initialization & URL generation
# ----------------------------------------------------------------------


def test_init_with_explicit_dependencies(
    service: AuthFlowService,
    mock_settings: SimpleNamespace,
    mocks: dict[str, MagicMock],
) -> None:
    assert service.app_settings is mock_settings
    assert service.oauth_service is mocks["oauth_service"]
    assert service.token_manager is mocks["token_manager"]
    assert service.user_svc is mocks["user_svc"]
    assert service.token_signer is mocks["token_signer"]
    assert service.request_secret_key == "oauth_request_secret"
    assert service.request_token_key == "oauth_token"
    assert service.oauth_state_nonce == "oauth_state_nonce"


def test_init_with_defaults(mock_settings: SimpleNamespace) -> None:
    # Verify default wiring builds collaborators using settings values.
    with (
        patch("src.main_app.services.auth.flow.get_settings", return_value=mock_settings),
        patch("src.main_app.services.auth.flow.OAuthService") as mock_oauth_cls,
        patch("src.main_app.services.auth.flow.TokenManager") as mock_tm_cls,
        patch("src.main_app.services.auth.flow.UsersService") as mock_us_cls,
        patch("src.main_app.services.auth.flow.SignedTokenService") as mock_ts_cls,
    ):
        svc = AuthFlowService()

        mock_oauth_cls.assert_called_once_with(
            consumer_key="consumer-key",
            consumer_secret="consumer-secret",
            oauth_mwuri="https://meta.wikimedia.org/w/index.php",
            user_agent="TestUserAgent/1.0",
        )
        mock_tm_cls.assert_called_once_with()
        mock_us_cls.assert_called_once_with()
        mock_ts_cls.assert_called_once_with()
        assert svc.app_settings is mock_settings


def test_build_callback_url(app: Flask, service: AuthFlowService) -> None:
    with app.test_request_context("/"):
        url = service.build_callback_url("state-xyz")

    assert "state=state-xyz" in url
    assert "/auth/callback" in url


# ----------------------------------------------------------------------
# start_login
# ----------------------------------------------------------------------


def test_start_login_success(
    app: Flask,
    service: AuthFlowService,
    mocks: dict[str, MagicMock],
) -> None:
    with app.test_request_context("/"):
        with patch("src.main_app.services.auth.flow.secrets.token_urlsafe", return_value="fixed-nonce"):
            result = service.start_login()

        assert result.success is True
        assert result.redirect_url == "https://meta.wikimedia.org/oauth/authorize?oauth_token=req_tok"
        assert session["oauth_state_nonce"] == "fixed-nonce"
        assert session["oauth_token"] == "req_tok"
        assert session["oauth_request_secret"] == "req_sec"

        mocks["token_signer"].sign_state_token.assert_called_once_with("fixed-nonce")
        mocks["oauth_service"].create_authorization_url.assert_called_once()
        callback_arg = mocks["oauth_service"].create_authorization_url.call_args[0][0]
        assert "state=signed:fixed-nonce" in callback_arg


def test_start_login_raises_returns_failure(
    app: Flask,
    service: AuthFlowService,
    mocks: dict[str, MagicMock],
) -> None:
    mocks["oauth_service"].create_authorization_url.side_effect = RuntimeError("OAuth provider down")

    with app.test_request_context("/"):
        result = service.start_login()

    assert result.success is False
    assert result.error_message == "Failed to initiate OAuth login"
    assert result.flash_category == "danger"


# ----------------------------------------------------------------------
# complete_callback
# ----------------------------------------------------------------------


def test_complete_callback_success(
    app: Flask,
    service: AuthFlowService,
    mocks: dict[str, MagicMock],
) -> None:
    with app.test_request_context("/"):
        session["oauth_state_nonce"] = "nonce-123"
        session["oauth_token"] = "req_tok"
        session["oauth_request_secret"] = "req_sec"

        request_args = {
            "oauth_token": "signed:nonce-123",
            "oauth_verifier": "verifier-abc",
        }
        result = service.complete_callback(request_args=request_args, post_login_redirect="/dashboard")

        assert result.success is True
        assert result.response is not None
        assert result.response.status_code == 302
        assert result.response.headers["Location"] == "/dashboard"

        assert session["uid"] == 42
        assert session["username"] == "WikiEditor"
        assert g._current_user.user_id == 42

        # Verify cookie was set with expected attributes
        set_cookie_headers = result.response.headers.getlist("Set-Cookie")
        assert any("auth_token=signed_uid%3A42" in h or "auth_token=signed_uid:42" in h for h in set_cookie_headers)

        mocks["oauth_service"].fetch_access_token.assert_called_once_with(
            query_string="oauth_token=signed%3Anonce-123&oauth_verifier=verifier-abc",
            oauth_token="req_tok",
            oauth_token_secret="req_sec",
        )
        mocks["user_svc"].ensure_exists.assert_called_once_with("WikiEditor")
        mocks["token_manager"].save_token.assert_called_once_with(
            user_id=42,
            access_token="acc_key",
            access_secret="acc_secret",
        )
        mocks["token_manager"].get_authenticated_user.assert_called_once_with(42)


def test_complete_callback_identity_falls_back_to_name(
    app: Flask,
    service: AuthFlowService,
    mocks: dict[str, MagicMock],
) -> None:
    mocks["oauth_service"].identify.return_value = {"name": "FallbackUser"}

    with app.test_request_context("/"):
        session["oauth_state_nonce"] = "nonce-123"
        session["oauth_token"] = "req_tok"
        session["oauth_request_secret"] = "req_sec"

        result = service.complete_callback(
            request_args={"oauth_token": "signed:nonce-123", "oauth_verifier": "ver"},
            post_login_redirect="/",
        )

        assert result.success is True
        assert session["username"] == "FallbackUser"


@pytest.mark.parametrize(
    ("session_state", "returned_state", "verified_return", "expected_msg"),
    [
        (None, "signed:abc", "abc", "Invalid OAuth state"),
        ("abc", None, "abc", "Invalid OAuth state"),
        ("abc", "signed:wrong", "wrong", "oauth-state-mismatch"),
    ],
)
def test_complete_callback_state_verification_failures(
    app: Flask,
    service: AuthFlowService,
    mocks: dict[str, MagicMock],
    session_state: str | None,
    returned_state: str | None,
    verified_return: str,
    expected_msg: str,
) -> None:
    mocks["token_signer"].verify_state_token.side_effect = None
    mocks["token_signer"].verify_state_token.return_value = verified_return

    with app.test_request_context("/"):
        if session_state is not None:
            session["oauth_state_nonce"] = session_state

        args: dict[str, str] = {"oauth_verifier": "ver"}
        if returned_state is not None:
            args["oauth_token"] = returned_state

        result = service.complete_callback(request_args=args, post_login_redirect="/")

        assert result.success is False
        assert result.error_message == expected_msg
        assert result.flash_category == "danger"


@pytest.mark.parametrize(
    ("sess_tok", "sess_sec", "verifier"),
    [
        (None, "req_sec", "ver"),
        ("req_tok", None, "ver"),
        ("req_tok", "req_sec", None),
        ("req_tok", "req_sec", ""),
    ],
)
def test_complete_callback_missing_token_or_verifier(
    app: Flask,
    service: AuthFlowService,
    sess_tok: str | None,
    sess_sec: str | None,
    verifier: str | None,
) -> None:
    with app.test_request_context("/"):
        session["oauth_state_nonce"] = "nonce-1"
        if sess_tok is not None:
            session["oauth_token"] = sess_tok
        if sess_sec is not None:
            session["oauth_request_secret"] = sess_sec

        args: dict[str, str] = {"oauth_token": "signed:nonce-1"}
        if verifier is not None:
            args["oauth_verifier"] = verifier

        result = service.complete_callback(request_args=args, post_login_redirect="/")

        assert result.success is False
        assert result.error_message == "Invalid OAuth verifier"
        assert result.flash_category == "danger"


def test_complete_callback_fetch_access_token_oauth_callback_error(
    app: Flask,
    service: AuthFlowService,
    mocks: dict[str, MagicMock],
) -> None:
    mocks["oauth_service"].fetch_access_token.side_effect = OAuthCallbackError(
        "Token exchange rejected",
        flash_category="warning",
    )

    with app.test_request_context("/"):
        session["oauth_state_nonce"] = "nonce-1"
        session["oauth_token"] = "req_tok"
        session["oauth_request_secret"] = "req_sec"

        result = service.complete_callback(
            request_args={"oauth_token": "signed:nonce-1", "oauth_verifier": "ver"},
            post_login_redirect="/",
        )

        assert result.success is False
        assert result.error_message == "Token exchange rejected"
        assert result.flash_category == "warning"


def test_complete_callback_fetch_access_token_unexpected_error(
    app: Flask,
    service: AuthFlowService,
    mocks: dict[str, MagicMock],
) -> None:
    mocks["oauth_service"].fetch_access_token.side_effect = ConnectionError("Network timeout")

    with app.test_request_context("/"):
        session["oauth_state_nonce"] = "nonce-1"
        session["oauth_token"] = "req_tok"
        session["oauth_request_secret"] = "req_sec"

        result = service.complete_callback(
            request_args={"oauth_token": "signed:nonce-1", "oauth_verifier": "ver"},
            post_login_redirect="/",
        )

        assert result.success is False
        assert result.error_message == "OAuth login failed. Please try again."
        assert result.flash_category == "danger"


def test_complete_callback_identify_errors(
    app: Flask,
    service: AuthFlowService,
    mocks: dict[str, MagicMock],
) -> None:
    with app.test_request_context("/"):
        session["oauth_state_nonce"] = "nonce-1"
        session["oauth_token"] = "req_tok"
        session["oauth_request_secret"] = "req_sec"

        mocks["oauth_service"].identify.side_effect = OAuthIdentityError("Bad identity")
        res_id_err = service.complete_callback(
            request_args={"oauth_token": "signed:nonce-1", "oauth_verifier": "ver"},
            post_login_redirect="/",
        )
        assert res_id_err.success is False
        assert res_id_err.error_message == "Failed to verify OAuth identity"
        assert res_id_err.flash_category == "danger"

    with app.test_request_context("/"):
        session["oauth_state_nonce"] = "nonce-2"
        session["oauth_token"] = "req_tok"
        session["oauth_request_secret"] = "req_sec"

        mocks["oauth_service"].identify.side_effect = OAuthCallbackError(
            "Callback identity error",
            flash_category="info",
        )
        res_cb_err = service.complete_callback(
            request_args={"oauth_token": "signed:nonce-2", "oauth_verifier": "ver"},
            post_login_redirect="/",
        )
        assert res_cb_err.success is False
        assert res_cb_err.error_message == "Callback identity error"
        assert res_cb_err.flash_category == "info"


def test_complete_callback_missing_username(
    app: Flask,
    service: AuthFlowService,
    mocks: dict[str, MagicMock],
) -> None:
    mocks["oauth_service"].identify.return_value = {}

    with app.test_request_context("/"):
        session["oauth_state_nonce"] = "nonce-1"
        session["oauth_token"] = "req_tok"
        session["oauth_request_secret"] = "req_sec"

        result = service.complete_callback(
            request_args={"oauth_token": "signed:nonce-1", "oauth_verifier": "ver"},
            post_login_redirect="/",
        )

        assert result.success is False
        assert result.error_message == "Missing username in OAuth identity"
        assert result.flash_category == "danger"


def test_complete_callback_resolve_user_id_failure(
    app: Flask,
    service: AuthFlowService,
    mocks: dict[str, MagicMock],
) -> None:
    mocks["user_svc"].ensure_exists.side_effect = RuntimeError("DB unavailable")

    with app.test_request_context("/"):
        session["oauth_state_nonce"] = "nonce-1"
        session["oauth_token"] = "req_tok"
        session["oauth_request_secret"] = "req_sec"

        result = service.complete_callback(
            request_args={"oauth_token": "signed:nonce-1", "oauth_verifier": "ver"},
            post_login_redirect="/",
        )

        assert result.success is False
        assert result.error_message == "Failed to resolve user ID"
        assert result.flash_category == "danger"


def test_complete_callback_save_or_load_token_failure(
    app: Flask,
    service: AuthFlowService,
    mocks: dict[str, MagicMock],
) -> None:
    # Case A: save_token returns None
    mocks["token_manager"].save_token.return_value = None
    with app.test_request_context("/"):
        session["oauth_state_nonce"] = "nonce-1"
        session["oauth_token"] = "req_tok"
        session["oauth_request_secret"] = "req_sec"

        res_save = service.complete_callback(
            request_args={"oauth_token": "signed:nonce-1", "oauth_verifier": "ver"},
            post_login_redirect="/",
        )
        assert res_save.success is False
        assert res_save.error_message == "Failed to save user credentials"
        assert res_save.flash_category == "danger"

    # Case B: save_token succeeds, get_authenticated_user returns None
    mocks["token_manager"].save_token.return_value = SimpleNamespace(id=1)
    mocks["token_manager"].get_authenticated_user.return_value = None
    with app.test_request_context("/"):
        session["oauth_state_nonce"] = "nonce-2"
        session["oauth_token"] = "req_tok"
        session["oauth_request_secret"] = "req_sec"

        res_load = service.complete_callback(
            request_args={"oauth_token": "signed:nonce-2", "oauth_verifier": "ver"},
            post_login_redirect="/",
        )
        assert res_load.success is False
        assert res_load.error_message == "Failed to load user credentials"
        assert res_load.flash_category == "danger"


# ----------------------------------------------------------------------
# logout
# ----------------------------------------------------------------------


def test_logout_with_session_uid(
    app: Flask,
    service: AuthFlowService,
    mocks: dict[str, MagicMock],
) -> None:
    with app.test_request_context("/"):
        session["uid"] = 42
        session["username"] = "WikiEditor"
        session["oauth_token"] = "req_tok"
        session["oauth_request_secret"] = "req_sec"
        session["oauth_state_nonce"] = "state_nonce"
        g._current_user = SimpleNamespace(user_id=42)

        result = service.logout(
            session_uid=42,
            cookie_value="ignored-cookie",
            index_url="/home",
        )

        assert result.message == "You have been logged out successfully."
        assert result.flash_category == "info"
        assert result.response.status_code == 302
        assert result.response.headers["Location"] == "/home"
        assert g._current_user is None

        for key in ("uid", "username", "oauth_token", "oauth_request_secret", "oauth_state_nonce"):
            assert key not in session

        mocks["token_signer"].extract_user_id.assert_not_called()
        mocks["token_manager"].delete_token.assert_called_once_with(42)


def test_logout_extracts_uid_from_cookie_when_session_uid_missing(
    app: Flask,
    service: AuthFlowService,
    mocks: dict[str, MagicMock],
) -> None:
    with app.test_request_context("/"):
        result = service.logout(
            session_uid=None,
            cookie_value="signed_uid:42",
            index_url="/",
        )

        assert result.message == "You have been logged out successfully."
        assert result.flash_category == "info"
        mocks["token_signer"].extract_user_id.assert_called_once_with("signed_uid:42")
        mocks["token_manager"].delete_token.assert_called_once_with(42)


def test_logout_without_uid_clears_session_only(
    app: Flask,
    service: AuthFlowService,
    mocks: dict[str, MagicMock],
) -> None:
    mocks["token_signer"].extract_user_id.return_value = None

    with app.test_request_context("/"):
        result = service.logout(
            session_uid=None,
            cookie_value=None,
            index_url="/",
        )

        assert result.message == "Session cleared."
        assert result.flash_category == "info"
        mocks["token_manager"].delete_token.assert_not_called()


def test_logout_delete_token_error_sets_danger_flash(
    app: Flask,
    service: AuthFlowService,
    mocks: dict[str, MagicMock],
) -> None:
    mocks["token_manager"].delete_token.side_effect = RuntimeError("Failed to revoke token")

    with app.test_request_context("/"):
        result = service.logout(
            session_uid=42,
            cookie_value=None,
            index_url="/",
        )

        assert result.message == "Error while clearing OAuth credentials."
        assert result.flash_category == "danger"
        assert g._current_user is None
