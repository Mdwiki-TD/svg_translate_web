"""Base worker infrastructure with standardized lifecycle management."""

from __future__ import annotations

import logging

import click
from flask import Flask

from .jobs_worker import start_job_cli

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
        flask --app src/app1.py run-job collect_templates_data

        With update_all (True):
        flask --app src/app1.py run-job collect_templates_data --update-all
        """
        # Convert boolean to string ("true" or "false") to match your current format
        update_all_str = "true" if update_all else "false"

        start_job_cli(
            auth_payload={"username": "Background job"},
            job_type=job_type,
            args={"update_all": update_all_str},
            app=app,
        )


__all__ = [
    "register_cli_jobs",
]
