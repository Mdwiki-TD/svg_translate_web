"""CLI commands for running and managing background jobs."""

from __future__ import annotations

import logging

import click
from flask import Flask

from .jobs_lifetime.jobs_starter import JobStarter

logger = logging.getLogger(__name__)


def register_cli_jobs(app: Flask) -> None:

    @app.cli.command("run-job")
    @click.argument("job_type")
    # Adds an optional flag --update-all (default is False if not provided)
    @click.option("--update-all", is_flag=True, help="Set to True if you want to update all.")
    def _run_job(job_type: str, update_all: bool) -> None:
        """
        How to test locally:
        .venv/Scripts/activate

        Without update_all (False):
        flask --app "$HOME/www/python/src/app.py" run-job collect_templates_data

        With update_all (True):
        flask --app "$HOME/www/python/src/app.py" run-job collect_templates_data --update-all
        """
        # Convert boolean to string ("true" or "false") to match your current format
        update_all_str = "true" if update_all else "false"

        JobStarter().start_cli(
            auth_payload={"username": "Background job"},
            job_type=job_type,
            args={"update_all": update_all_str},
            app=app,
        )

    @app.cli.command("dispatch-jobs")
    def _dispatch_jobs() -> None:
        """Recover the job queue: release stale slots and start pending jobs.

        Intended for periodic execution (cron / toolforge-jobs schedule) so a
        job persisted before a crash or restart is never left waiting forever:

        flask --app "$HOME/www/python/src/app.py" dispatch-jobs
        """
        from .jobs_lifetime.jobs_queue import JobsQueue

        dispatched = JobsQueue().recover(force=True)
        click.echo(f"Dispatched {len(dispatched)} pending job(s): {dispatched}")


__all__ = [
    "register_cli_jobs",
]
