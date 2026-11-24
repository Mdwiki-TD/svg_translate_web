# src/main_app/jobs/registry.py
"""Single source of truth for resolving a job type to its ``JobData``."""

from __future__ import annotations

from ..jobs_workers.objects import JobData
from ..jobs_workers.workers_lists import jobs_data_admins, jobs_data_public


def load_job_data(job_type: str) -> JobData | None:
    """Return the ``JobData`` registered for ``job_type`` (admin jobs first, then public)."""
    return jobs_data_admins.get(job_type) or jobs_data_public.get(job_type)


__all__ = [
    "load_job_data",
]
