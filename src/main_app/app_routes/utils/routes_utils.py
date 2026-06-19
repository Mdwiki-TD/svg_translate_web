#
from __future__ import annotations

import logging
from typing import Any, Dict

from flask import url_for

from ...jobs_workers.public_jobs_workers.workers_list_public import jobs_data_public
from ..auth.utils import load_user

logger = logging.getLogger(__name__)


def _is_admin(user: Any) -> bool:
    """Check if user is an active coordinator (admin)."""
    return bool(user and getattr(user, "is_active_admin", False))


def context_user(
    wiki_domain: str,
    static_server: str,
    tool_title: str = "",
) -> dict[str, Any]:
    """
    Used in @app.context_processor to inject variables into templates.
    """
    # Safe retrieval from g with a fallback to None
    user = load_user()

    username = user.username if user else None

    return {
        "is_authenticated": user is not None,
        "current_username": username,
        "is_admin": _is_admin(user),
        "wiki_domain": wiki_domain,
        "static_server": static_server,
        "tool_title": tool_title,
    }


def load_auth_payload(user: Any | None) -> Dict[str, Any]:
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


def can_run_jobs(user: Any) -> bool:
    """Return True if user may run synchronous edit jobs.

    Admins (active coordinators) always pass.
    """
    if _is_admin(user):
        return True
    return bool(user and user.can_run_jobs)


def can_run_bg_jobs(user: Any) -> bool:
    """Return True if user may run background (daemon) jobs.

    Admins (active coordinators) always pass.
    """
    if _is_admin(user):
        return True
    return bool(user and user.can_run_bg_jobs)


def get_job_detail_url(job_id: int, job_type: str) -> str:
    """Returns the correct job detail URL based on job type."""
    if job_type in jobs_data_public:
        return url_for("public_jobs.job_detail", job_type=job_type, job_id=job_id)
    return url_for("admin.jobs.job_detail", job_type=job_type, job_id=job_id)


__all__ = [
    "can_run_bg_jobs",
    "can_run_jobs",
    "context_user",
    "load_auth_payload",
    "get_job_detail_url",
]
