from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from ..services.auth.current_user_resolver import CurrentUserResolver

logger = logging.getLogger(__name__)


class RequestContextHelper:
    """Helper for request context, auth payload, and job permissions."""

    @classmethod
    def context_data(
        cls,
        wiki_domain: str,
        static_server: str,
        tool_title: str = "",
    ) -> dict[str, Any]:
        """Inject variables into templates."""
        # Safe retrieval from g with a fallback to None
        user = CurrentUserResolver.get_current_user()

        username = user.username if user else None

        yesterday = (date.today() - timedelta(days=1)).isoformat()
        return {
            "tool_title": tool_title,
            "is_authenticated": user is not None,
            "current_username": username,
            "is_admin": cls._is_admin(user),
            "is_coordinator": cls._is_coordinator(user),
            "wiki_domain": wiki_domain,
            "static_server": static_server,
            "yesterday": yesterday,
        }

    @staticmethod
    def load_auth_payload(user: Any | None) -> dict[str, Any]:
        """Extract auth dict from user object."""
        if user and hasattr(user, "to_auth_payload"):
            return user.to_auth_payload()
        if user:
            access_key, access_secret = user.access_token, user.access_secret
            return {
                "id": user.user_id,
                "username": user.username,
                "access_token": access_key,
                "access_secret": access_secret,
            }
        return {}

    @classmethod
    def can_run_jobs(cls, user: Any) -> bool:
        """Check if user may run synchronous edit jobs."""
        if cls._is_admin(user):
            return True
        return bool(user and user.can_run_jobs)

    @classmethod
    def can_run_bg_jobs(cls, user: Any) -> bool:
        """Check if user may run background (daemon) jobs."""
        if cls._is_admin(user):
            return True
        return bool(user and user.can_run_bg_jobs)

    @staticmethod
    def _is_admin(user: Any) -> bool:
        """Check if user is an active admin."""
        return bool(user and getattr(user, "is_active_admin", False))

    @staticmethod
    def _is_coordinator(user: Any) -> bool:
        """Check if user is an active coordinator."""
        return bool(user and getattr(user, "is_active_coordinator", False))


__all__ = [
    "RequestContextHelper",
]
