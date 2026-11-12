from __future__ import annotations

import logging
from typing import Any

from flask import url_for

from ..jobs_workers.public_jobs_workers.workers_list_public import jobs_data_public
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

        return {
            "is_authenticated": user is not None,
            "current_username": username,
            "is_admin": cls._is_admin(user),
            "wiki_domain": wiki_domain,
            "static_server": static_server,
            "tool_title": tool_title,
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
    def get_job_detail_url(job_id: int, job_type: str) -> str:
        """Returns the correct job detail URL based on job type."""
        if job_type in jobs_data_public:
            return url_for("public_jobs.job_detail", job_type=job_type, job_id=job_id)
        return url_for("admin_panel.jobs.job_detail", job_type=job_type, job_id=job_id)


can_run_bg_jobs = RequestContextHelper.can_run_bg_jobs
can_run_jobs = RequestContextHelper.can_run_jobs
context_data = RequestContextHelper.context_data
load_auth_payload = RequestContextHelper.load_auth_payload
get_job_detail_url = RequestContextHelper.get_job_detail_url

__all__ = [
    "RequestContextHelper",
    "can_run_bg_jobs",
    "can_run_jobs",
    "context_data",
    "load_auth_payload",
    "get_job_detail_url",
]
