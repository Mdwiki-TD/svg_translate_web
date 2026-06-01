"""Composite user identity + credentials for request handling."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CurrentUser:
    """Bundles user identity (from ``users`` table) and OAuth credentials
    (from ``user_tokens`` table) into a single object for request handling.

    Stored in ``g._current_user`` during the request lifecycle.
    """

    user_id: int
    username: str
    access_token: bytes
    access_secret: bytes
    can_run_jobs: bool = False
    can_run_bg_jobs: bool = False
    is_active_admin: bool = False

    def to_auth_payload(self) -> dict[str, int | str | bytes]:
        """Return the dict expected by ``api_services/clients/wiki_client``."""
        return {
            "id": self.user_id,
            "username": self.username,
            "access_token": self.access_token,
            "access_secret": self.access_secret,
        }


__all__ = [
    "CurrentUser",
]
