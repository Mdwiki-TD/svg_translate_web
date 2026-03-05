"""APScheduler BackgroundScheduler configuration for cron jobs."""

from __future__ import annotations
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

from .jobs_workers import jobs_worker

logger = logging.getLogger(__name__)

# Scheduler singleton
_scheduler: BackgroundScheduler | None = None


class Config:
    """Scheduler configuration."""

    SCHEDULER_API_ENABLED = False
    SCHEDULER_EXECUTORS = {
        "default": {"type": "threadpool", "max_workers": 1},
    }
    SCHEDULER_JOB_DEFAULTS = {
        "coalesce": True,
        "max_instances": 1,
        "misfire_grace_time": 3600,  # 1 hour grace period
    }


def collect_main_files_job() -> None:
    """Scheduled job to collect main files."""
    logger.info("Starting scheduled collect_main_files job")
    try:
        job_id = jobs_worker.start_job(user=None, job_type="collect_main_files")
        logger.info(f"Scheduled collect_main_files job started with ID {job_id}")
    except Exception:
        logger.exception("Failed to start scheduled collect_main_files job")


def init_scheduler(app: Flask) -> BackgroundScheduler | None:
    """
    Initialize and start the BackgroundScheduler.

    Args:
        app: Flask application instance (kept for API compatibility)

    Returns:
        BackgroundScheduler instance or None if initialization fails
    """
    global _scheduler

    if _scheduler is not None:
        return _scheduler

    try:
        # Create BackgroundScheduler with config
        scheduler = BackgroundScheduler(
            executors=Config.SCHEDULER_EXECUTORS,
            job_defaults=Config.SCHEDULER_JOB_DEFAULTS,
        )

        # Add daily job at 3:00 AM
        scheduler.add_job(
            collect_main_files_job,
            trigger="cron",
            hour=3,
            minute=0,
            id="collect_main_files_daily",
            replace_existing=True,
        )
        logger.info("Scheduled collect_main_files job: daily at 03:00")

        scheduler.start()
        _scheduler = scheduler
        logger.info("BackgroundScheduler started successfully")

        return scheduler

    except Exception:
        logger.exception("Failed to initialize BackgroundScheduler")
        return None


def shutdown_scheduler() -> None:
    """Shutdown the scheduler."""
    global _scheduler
    if _scheduler is not None:
        try:
            _scheduler.shutdown()
            logger.info("BackgroundScheduler shut down successfully")
        except Exception:
            logger.exception("Error shutting down BackgroundScheduler")
        finally:
            _scheduler = None
