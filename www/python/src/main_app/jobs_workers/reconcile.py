"""Reconciliation: sync DB state with Toolforge and clean up finished jobs."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from requests import HTTPError

from ..api_services.clients.toolforge import ToolforgeJobsService
from ..config import get_settings
from ..database.services import JobsService
from .admin_jobs_workers.workers_list import jobs_data_admins
from .backends.toolforge_backend import tf_job_name

logger = logging.getLogger(__name__)

GRACE = timedelta(seconds=90)  # Time before considering a missing job as lost


def get_live_status(job) -> dict | None:
    """Query Toolforge for the live status of a single job."""
    tf = ToolforgeJobsService()
    name = tf_job_name(job.job_type, job.id)
    try:
        tf_job = tf.show_job(name)["job"]
    except HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise
    status = tf_job.get("status", {})
    return {
        "short": status.get("short", "unknown"),
        "duration": status.get("duration"),
        "messages": status.get("messages", []),
        "detail": tf_job.get("status_long"),
    }


def running_jobs():
    """Return active DB rows paired with their live Toolforge state."""
    tf = ToolforgeJobsService()
    live = {j["name"]: j for j in tf.list_jobs().get("jobs", [])}
    rows = JobsService().list_active(backend="toolforge")
    return [(row, live.get(tf_job_name(row.job_type, row.id))) for row in rows]


def sync_job(job) -> None:
    """Synchronize a single DB row with its Toolforge state."""
    svc = JobsService()
    live = get_live_status(job)
    if live is None:
        created = job.created_at
        if created and created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        if created and datetime.now(UTC) - created > GRACE:
            svc.mark_failed(job, "job is missing in Toolforge")
    elif live["short"] == "failed":
        svc.mark_failed(job, "; ".join(live["messages"]))
    elif live["short"] == "succeeded" and job.status in ("pending", "running"):
        svc.mark_as_completed(job)
    elif live["short"] == "running" and job.status == "pending":
        svc.update_job_status(job.id, "running", job_type=job.job_type)


def reconcile() -> None:
    """Main reconciliation loop: sync active jobs and clean up finished ones."""
    svc = JobsService()

    # Sync active toolforge jobs
    for job in svc.list_active(backend="toolforge"):
        try:
            sync_job(job)
        except Exception:
            logger.exception("Failed to sync job %s", job.id)

    # Clean up finished Toolforge jobs
    tf = ToolforgeJobsService()
    try:
        all_tf_jobs = tf.list_jobs().get("jobs", [])
    except Exception:
        logger.exception("Failed to list Toolforge jobs for cleanup")
        return

    # Only clean up jobs whose names match known job types
    known_types = set(jobs_data_admins.keys())

    for tf_job in all_tf_jobs:
        if tf_job.get("status", {}).get("short") not in ("succeeded", "failed"):
            continue
        name = tf_job.get("name", "")
        # Extract job_id from name (format: <type-slug>-<id>)
        try:
            job_id = int(name.rsplit("-", 1)[-1])
        except (ValueError, IndexError):
            continue
        row = svc.get_by(id=job_id)
        if row and row.status in svc.FINAL_STATUSES:
            try:
                tf.delete_job(name)
                logger.info("Cleaned up finished Toolforge job '%s'", name)
            except HTTPError:
                logger.exception("Cleanup failed for %s", name)


def setup_reconcile_schedule() -> None:
    """Create or update the scheduled reconcile job on Toolforge."""
    tf = ToolforgeJobsService()
    app_settings = get_settings()
    jobs_cfg = app_settings.jobs

    tf.update_job(
        {
            "name": "reconcile-jobs",
            "imagename": jobs_cfg.toolforge_job_image,
            "job_type": "scheduled",
            "schedule": "*/5 * * * *",
            "cmd": f"bash {jobs_cfg.toolforge_job_script} reconcile-jobs",
            "mount": "all",
            "memory": "512Mi",
            "cpu": "0.2",
        }
    )
    logger.info("Scheduled reconcile-jobs on Toolforge")


__all__ = [
    "reconcile",
    "sync_job",
    "get_live_status",
    "running_jobs",
    "setup_reconcile_schedule",
]
