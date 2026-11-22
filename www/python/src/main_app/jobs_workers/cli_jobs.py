"""CLI commands for running and managing background jobs."""

from __future__ import annotations

import logging
import sys

import click
from flask import Flask

from .jobs_lifetime.jobs_starter import JobStarter
from .run_job import run_job_by_id

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

    @app.cli.command("run-job-id")
    @click.argument("job_id", type=int)
    def _run_job_id(job_id: int) -> None:
        """Run a single job by its database ID.

        Usage:
            flask --app "$HOME/www/python/src/app.py" run-job-id 123

        This is the entry point used by Toolforge one-off pods.
        The job record must already exist in the database (created by the web UI).
        """
        sys.exit(run_job_by_id(job_id))

    @app.cli.command("reconcile-jobs")
    def _reconcile_jobs() -> None:
        """Synchronize job DB state with Toolforge and clean up finished jobs.

        Usage:
            flask --app "$HOME/www/python/src/app.py" reconcile-jobs
        """
        from .reconcile import reconcile

        reconcile()


__all__ = [
    "register_cli_jobs",
]
