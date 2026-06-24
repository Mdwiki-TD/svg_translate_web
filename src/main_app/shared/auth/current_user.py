"""
Helpers for loading the current authenticated user.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CurrentUser:
    """Bundles user identity and OAuth credentials
    Stored in ``g._current_user`` during the request lifecycle.
    """

    user_id: int
    username: str
    access_token: bytes = field(repr=False)
    access_secret: bytes = field(repr=False)
    is_active_admin: bool = False
    can_run_jobs: bool = False
    can_run_bg_jobs: bool = False

    def to_auth_payload(self) -> dict[str, int | str | bytes]:
        return {
            "id": self.user_id,
            "username": self.username,
            "access_token": self.access_token,
            "access_secret": self.access_secret,
        }


__all__ = [
    "CurrentUser",
]
