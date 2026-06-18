"""Admin routes for managing background jobs."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def can_manage_job(job: Any, user: Any) -> bool:
    """Check if the current user can manage (cancel/delete) a job.

    Returns True if the user is an admin (coordinator) or if the user
    is the owner of the job.
    """
    if not user:
        return False
    if getattr(user, "is_active_admin", False):
        return True
    job_username = getattr(job, "username", None)
    if job_username and job_username == user.username:
        return True
    return False


__all__ = [
    "can_manage_job",
]
