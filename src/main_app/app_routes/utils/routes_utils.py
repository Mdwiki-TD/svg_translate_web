#
from __future__ import annotations

import logging
from typing import Any, Dict

from flask import g, url_for

from ...public_jobs_workers.workers_list_public import jobs_data_public

logger = logging.getLogger(__name__)


def _is_admin(user: Any) -> bool:
    """Check if user is an active coordinator (admin)."""
    return bool(user and getattr(user, "is_active_admin", False))


def context_user(wiki_domain: str, static_server: str) -> dict[str, Any]:
    """
    Used in @app.context_processor to inject variables into templates.
    """
    # Safe retrieval from g with a fallback to None
    user = getattr(g, "_current_user", None)

    username = user.username if user else None

    return {
        "is_authenticated": user is not None,
        "current_username": username,
        "is_admin": _is_admin(user),
        "wiki_domain": wiki_domain,
        "static_server": static_server,
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


def get_job_detail_url(job_id: int, job_type: str) -> str:
    """Returns the correct job detail URL based on job type."""
    if job_type in jobs_data_public:
        return url_for("public_jobs.job_detail", job_type=job_type, job_id=job_id)
    return url_for("admin.jobs.job_detail", job_type=job_type, job_id=job_id)


__all__ = [
    "context_user",
    "load_auth_payload",
    "get_job_detail_url",
]
