"""Admin routes for managing background jobs."""

from __future__ import annotations

import copy
import logging
from typing import Any

from ..su_services import load_job_result, save_job_result_by_name
from .admin_routes.results_utils import fix_result_data

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


def load_job_result_and_fix(result_file: str, job_type: str) -> dict[str, Any] | None:
    data = load_job_result(result_file)
    if data:
        data_before = copy.deepcopy(data)
        data2 = fix_result_data(data, job_type)
        if data2 != data_before:
            logger.info(f"Job result {result_file} was fixed")
            save_job_result_by_name(result_file, data2)
        else:
            logger.info(f"Job result {result_file} was not fixed")
        return data2

    return data


__all__ = [
    "can_manage_job",
    "load_job_result_and_fix",
]
