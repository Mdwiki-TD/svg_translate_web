"""
Helpers for loading the current authenticated user.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...database.models import UserTokenRecord


def parse_bool(value: str | int) -> bool:
    """Parse boolean value from CSV string."""
    if not value:
        return False
    if isinstance(value, int):
        value = str(value)
    return value.strip().lower() in {"yes", "true", "1", "y"}


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

    def __init__(self, **kwargs: Any) -> None:
        fields = self.__dataclass_fields__
        for key, value in kwargs.items():
            if key in fields:
                if key in ("can_run_jobs", "can_run_bg_jobs"):
                    value = parse_bool(value)
                object.__setattr__(self, key, value)

    def to_auth_payload(self) -> dict[str, int | str | bytes]:
        return {
            "id": self.user_id,
            "username": self.username,
            "access_token": self.access_token,
            "access_secret": self.access_secret,
        }

    @classmethod
    def from_authenticated(cls, token: UserTokenRecord, is_active_admin: bool) -> CurrentUser:
        return cls(
            user_id=token.user_id,
            username=token.user.username,
            access_token=token.access_token,
            access_secret=token.access_secret,
            is_active_admin=is_active_admin,
            can_run_jobs=token.user.can_run_jobs,
            can_run_bg_jobs=token.user.can_run_bg_jobs,
        )


__all__ = [
    "CurrentUser",
]
