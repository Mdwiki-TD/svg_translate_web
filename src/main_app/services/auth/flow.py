"""
AuthFlowService — orchestrates login, OAuth callback, and logout.

Keeps HTTP concerns (flash, redirect construction, rate limits) in the
route layer. This service owns session state, OAuth handshake steps,
token persistence, and cookie signing.
"""

from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from flask import g, make_response, redirect, session, url_for
from mwoauth import AccessToken
from werkzeug.wrappers import Response as WerkzeugResponse

from ...config import settings
from ...database.services import UsersService
from ..core.cookies import (
    extract_user_id,
    sign_state_token,
    sign_user_id,
    verify_state_token,
)
from .auth_exceptions import OAuthCallbackError, OAuthIdentityError
from .auth_service import OAuthService
from .token_manager import TokenManager

logger = logging.getLogger(__name__)

request_secret_key = settings.sessions.request_secret_key
request_token_key = settings.sessions.request_token_key
oauth_state_nonce = settings.sessions.state_key


@dataclass(frozen=True)
class LoginStartResult:
    """Outcome of starting the OAuth login flow."""

    success: bool
    redirect_url: str | None = None
    error_message: str | None = None
    flash_category: str = "danger"


@dataclass(frozen=True)
class CallbackResult:
    """Outcome of completing the OAuth callback."""

    success: bool
    response: WerkzeugResponse | None = None
    error_message: str | None = None
    flash_category: str = "danger"


@dataclass(frozen=True)
class LogoutResult:
    """Outcome of logout."""

    response: WerkzeugResponse
    message: str
    flash_category: str = "info"


class AuthFlowService:
    """High-level orchestration for the OAuth login lifecycle."""

    def __init__(self) -> None:
        self.oauth_service = OAuthService(
            consumer_key=settings.oauth.consumer_key,
            consumer_secret=settings.oauth.consumer_secret,
            oauth_mwuri=settings.oauth.mw_uri,
            user_agent=settings.other.user_agent,
        )
        self.token_manager = TokenManager()
        self.user_svc = UsersService()

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    def build_callback_url(self, signed_state: str) -> str:
        return url_for(
            "auth.callback",
            _external=True,
            state=signed_state,
        )

    def start_login(
        self,
    ) -> LoginStartResult:
        """
        Begin OAuth flow.
        Stores request token + secret and state nonce in the session.
        """
        state_nonce = secrets.token_urlsafe(32)
        session[oauth_state_nonce] = state_nonce

        signed_state = sign_state_token(state_nonce)
        callback_url = self.build_callback_url(signed_state)

        try:
            auth_url, request_token, request_secret = self.oauth_service.create_authorization_url(callback_url)
            logger.info("OAuth login started successfully, redirecting to MediaWiki")
        except (RuntimeError, Exception):
            logger.exception("Failed to start OAuth login")
            return LoginStartResult(
                success=False,
                error_message="Failed to initiate OAuth login",
                flash_category="danger",
            )

        # ------------------
        # Store request token in session for the callback step
        session[request_token_key] = request_token
        session[request_secret_key] = request_secret

        logger.debug("OAuth request token stored in session")
        logger.info("OAuth login started successfully, redirecting to MediaWiki")

        return LoginStartResult(success=True, redirect_url=auth_url)

    # ------------------------------------------------------------------
    # Callback
    # ------------------------------------------------------------------

    def complete_callback(
        self,
        request_args: dict[str, Any],
        post_login_redirect: str,
    ) -> CallbackResult:
        """
        Validate state, exchange verifier for access token, identify user,
        persist credentials, set session + cookie.
        """
        # 1. State verification
        state_error = self._verify_oauth_state(request_args.get(settings.sessions.request_token_key))
        if state_error:
            return state_error

        # 2. Request token + verifier
        oauth_verifier = request_args.get("oauth_verifier")
        request_token = session.pop(request_token_key, None)
        request_secret = session.pop(request_secret_key, None)

        if not request_token or not request_secret or not oauth_verifier:
            logger.warning("OAuth callback failed: missing request token or verifier")
            return CallbackResult(
                success=False,
                error_message="Invalid OAuth verifier",
                flash_category="danger",
            )

        # 3. Exchange for access token
        query_string = urlencode(request_args)
        try:
            token_data: AccessToken = self.oauth_service.fetch_access_token(
                query_string=query_string,
                oauth_token=request_token,
                oauth_token_secret=request_secret,
            )
        except OAuthCallbackError as exc:
            logger.exception("OAuth callback failed: %s", exc)
            return CallbackResult(
                success=False,
                error_message=str(exc),
                flash_category=exc.flash_category,
            )
        except Exception as exc:
            logger.exception("OAuth callback failed: %s", exc)
            return CallbackResult(
                success=False,
                error_message="OAuth login failed. Please try again.",
                flash_category="danger",
            )

        # 4. Identify user
        try:
            identity = self.oauth_service.identify(token_data)
        except OAuthIdentityError:
            logger.exception("OAuth identity verification failed")
            return CallbackResult(
                success=False,
                error_message="Failed to verify OAuth identity",
                flash_category="danger",
            )
        except OAuthCallbackError as exc:
            logger.exception("OAuth callback failed: %s", exc)
            return CallbackResult(
                success=False,
                error_message=str(exc),
                flash_category=exc.flash_category,
            )

        username = identity.get("username") or identity.get("name") or ""
        if not username:
            logger.error("OAuth callback failed: missing username in identity")
            return CallbackResult(
                success=False,
                error_message="Missing username in OAuth identity",
                flash_category="danger",
            )

        # 5. Resolve / create user record
        try:
            user_id = self._resolve_user_id(username)
        except Exception as exc:
            logger.exception("Failed to resolve user ID: %s", exc)
            return CallbackResult(
                success=False,
                error_message="Failed to resolve user ID",
                flash_category="danger",
            )

        # 6. Persist encrypted token
        saved_token = self.token_manager.save_token(
            user_id=user_id,
            access_token=token_data.key,
            access_secret=token_data.secret,
        )
        if saved_token is None:
            logger.error("OAuth callback failed while saving user credentials")
            return CallbackResult(
                success=False,
                error_message="Failed to process user credentials",
                flash_category="danger",
            )

        user_record = self.token_manager.get_authenticated_user(user_id)
        if not user_record:
            logger.error("OAuth callback failed while saving user credentials")
            return CallbackResult(
                success=False,
                error_message="Failed to process user credentials",
                flash_category="danger",
            )

        # 7. Session + response cookies
        session["uid"] = user_id
        session["username"] = username

        # Set response and cookies
        response = make_response(redirect(post_login_redirect))
        self._set_auth_cookie(user_id, response)

        g._current_user = user_record

        return CallbackResult(success=True, response=response)

    def _verify_oauth_state(self, returned_state: str | None) -> CallbackResult | None:
        expected_state = session.pop(oauth_state_nonce, None)
        if not expected_state or not returned_state:
            logger.warning("OAuth callback failed: missing state token")
            return CallbackResult(
                success=False,
                error_message="Invalid OAuth state",
                flash_category="danger",
            )

        verified_state = verify_state_token(returned_state)
        if verified_state != expected_state:
            logger.warning("OAuth callback failed: state mismatch")
            return CallbackResult(
                success=False,
                error_message="oauth-state-mismatch",
                flash_category="danger",
            )
        return None

    def _resolve_user_id(self, username: str) -> int:
        """Return the user_id for ``username``, creating a UserRecord if needed."""
        record = self.user_svc.ensure_exists(username)
        return record.user_id

    @staticmethod
    def _set_auth_cookie(user_id: int, response: WerkzeugResponse) -> None:
        response.set_cookie(
            settings.cookie.name,
            sign_user_id(user_id),
            httponly=settings.cookie.httponly,
            secure=settings.cookie.secure,
            samesite=settings.cookie.samesite,
            max_age=settings.cookie.max_age,
            path="/",
        )

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    def logout(
        self,
        session_uid: int | None,
        cookie_value: str | None,
        index_url: str,
    ) -> LogoutResult:
        """Clear session, delete stored token, clear auth cookie."""
        user_id = session_uid

        session.pop("uid", None)
        session.pop(request_token_key, None)
        session.pop(request_secret_key, None)
        session.pop(oauth_state_nonce, None)
        session.pop("username", None)

        logger.info("Logout requested, user_id: %s", user_id)

        # extract user_id from signed cookie if needed
        if user_id is None and cookie_value:
            user_id = extract_user_id(cookie_value)
            logger.debug("Extracted user_id from cookie: %s", user_id)

        message = "Session cleared."
        flash_category = "info"

        # delete user token if possible
        if isinstance(user_id, int):
            try:
                self.token_manager.delete_token(user_id)
                message = "You have been logged out successfully."
                logger.info("User token deleted for user_id: %s", user_id)
            except Exception:
                logger.exception("Failed to delete user token during logout")
                message = "Error while clearing OAuth credentials."
                flash_category = "danger"

        response = make_response(redirect(index_url))
        response.delete_cookie(settings.cookie.name, path="/")
        g._current_user = None

        return LogoutResult(
            response=response,
            message=message,
            flash_category=flash_category,
        )


__all__ = [
    "AuthFlowService",
    "CallbackResult",
    "LoginStartResult",
    "LogoutResult",
]
