# src/main_app/jobs/job_user.py
"""Helpers for resolving the identity a job runs as."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


SYSTEM_USERNAME = "Background job"


def system_user() -> dict[str, Any]:
    """Return the identity used by jobs that need no user data (e.g. ``collect_templates_data``)."""
    return {"username": SYSTEM_USERNAME}


def build_job_user(username: str) -> dict | None:
    """Reconstruct the auth_payload dict from the database for a given username.

    Returns the same shape as ``CurrentUser.to_auth_payload()``:
    ``{id, username, access_token, access_secret}``.
    Returns None if the user has no token (deleted or never logged in).
    """
    from ..database.services.users.user_token_service import UserTokenService
    from ..services.auth.token_manager import TokenManager

    token = UserTokenService().get_user_token_by_username(username)
    if token is None:
        return None
    user = TokenManager().get_authenticated_user(token.user_id)
    return user.to_auth_payload() if user else None


__all__ = [
    "SYSTEM_USERNAME",
    "build_job_user",
    "system_user",
]
