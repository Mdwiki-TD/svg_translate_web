"""
APScheduler BackgroundScheduler configuration for background jobs."""

from __future__ import annotations
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

from .jobs_list import jobs_data
logger = logging.getLogger(__name__)

# Scheduler singleton
_scheduler: BackgroundScheduler | None = None


class Config:
    """
    Scheduler configuration.

    """

    SCHEDULER_API_ENABLED = False
    SCHEDULER_EXECUTORS = {
        "default": {"type": "threadpool", "max_workers": 1},
    }
    SCHEDULER_JOB_DEFAULTS = {
        "coalesce": True,
        "max_instances": 1,
        "misfire_grace_time": 3600,  # 1 hour grace period
    }


def init_scheduler(app: Flask) -> BackgroundScheduler | None:
    """
    Initialize and start the BackgroundScheduler.

    Args:
        app: Flask application instance (kept for API compatibility)

    Returns:
        BackgroundScheduler instance or None if initialization fails
    """
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        return _scheduler

    timezone = app.config.get("SCHEDULER_TIMEZONE", "UTC")
    try:
        # Create BackgroundScheduler with config
        scheduler = BackgroundScheduler(
            executors=Config.SCHEDULER_EXECUTORS,
            job_defaults=Config.SCHEDULER_JOB_DEFAULTS,
            timezone=timezone,
        )

    except Exception:
        logger.exception("Failed to initialize BackgroundScheduler")
        return None

    for job in jobs_data:
        job_time = f"{job.hour}{job.minute}"
        # Add daily job at 3:00 AM
        _job_scheduler = scheduler.add_job(
            job.func,
            trigger="cron",
            hour=job.hour,
            minute=job.minute,
            id=job.id,
            replace_existing=True,
        )
        job.job_scheduler = _job_scheduler
        logger.info(f"Scheduled {job.id} job: daily at {job_time}")

    scheduler.start()
    _scheduler = scheduler
    logger.info("BackgroundScheduler started successfully.")

    return scheduler


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
