# src/main_app/cli/cli_jobs.py
"""
CLI commands for running and managing background jobs.

Exit codes of ``run-job`` / ``run-job-id``:
    0 = success, 1 = job crashed, 2 = unknown job / not found, 3 = auth error, 4 = duplicate active job.
"""

from __future__ import annotations

import logging
import sys

import click
from flask import Flask

from ..database.exceptions import DuplicateRecordError
from .job_executor import JobExecutor
from .jobs_lifetime.jobs_starter import JobStarter

logger = logging.getLogger(__name__)

EXIT_DUPLICATE_JOB = 4


def register_cli_jobs(app: Flask) -> None:

    @app.cli.command("run-job")
    @click.argument("job_type")
    # Adds an optional flag --update-all (default is False if not provided)
    @click.option("--update-all", is_flag=True, help="Set to True if you want to update all.")
    def _run_job(job_type: str, update_all: bool) -> None:
        """Create and run a background job inline, in this process (no thread, no pod).

        How to test locally:
        .venv/Scripts/activate

        Without update_all (False):
        flask --app "$HOME/www/python/src/app.py" run-job collect_templates_data

        With update_all (True):
        flask --app "$HOME/www/python/src/app.py" run-job collect_templates_data --update-all
        """
        # Convert boolean to string ("true" or "false") to match the stored args format
        update_all_str = "true" if update_all else "false"

        try:
            exit_code = JobStarter().run_now(job_type, args={"update_all": update_all_str})
        except DuplicateRecordError:
            click.echo(f"A '{job_type}' job is already active; nothing was started.", err=True)
            sys.exit(EXIT_DUPLICATE_JOB)
        except ValueError as exc:
            click.echo(str(exc), err=True)
            sys.exit(2)

        sys.exit(exit_code)

    @app.cli.command("run-job-id")
    @click.argument("job_id", type=int)
    def _run_job_id(job_id: int) -> None:
        """Run a single job by its database ID.

        Usage:
            flask --app "$HOME/www/python/src/app.py" run-job-id 123

        This is the entry point used by Toolforge one-off pods.
        The job record must already exist in the database (created by the web UI).
        """
        sys.exit(JobExecutor().run(job_id, install_signal_handlers=True))

    @app.cli.command("reconcile-jobs")
    def _reconcile_jobs() -> None:
        """Synchronize job DB state with Toolforge and clean up finished jobs.

        Usage:
            flask --app "$HOME/www/python/src/app.py" reconcile-jobs
        """
        from .jobs_lifetime.reconcile import reconcile

        reconcile()


__all__ = [
    "register_cli_jobs",
]
