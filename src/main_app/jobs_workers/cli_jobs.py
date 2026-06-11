"""Base worker infrastructure with standardized lifecycle management."""

from __future__ import annotations

import logging

import click
from flask import Flask

from .jobs_worker import start_job_cli

logger = logging.getLogger(__name__)


def register_cli_jobs(app: Flask) -> None:
    @app.cli.command("run-collect-templates-data")
    def _run() -> None:
        """ """
        start_job_cli(
            user={"username": "Background job"},
            job_type="collect_templates_data",
            args={"update_all": "true"},
            app=app,
        )

    @app.cli.command("run-job")
    @click.argument("job_type")
    def _run_job(job_type: str) -> None:
        """
        how to test locally:
        .venv/Scripts/activate
        flask --app src/app1.py run-job collect_templates_data
        """
        start_job_cli(
            user={"username": "Background job"},
            job_type=job_type,
            args={"update_all": "false"},
            app=app,
        )


__all__ = [
    "register_cli_jobs",
]
