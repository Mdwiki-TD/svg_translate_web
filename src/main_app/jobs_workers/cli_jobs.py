"""Base worker infrastructure with standardized lifecycle management."""

from __future__ import annotations

import logging

from flask import Flask

from .jobs_worker import start_job_cli

logger = logging.getLogger(__name__)

def register_cli_jobs(app: Flask) -> None:
    @app.cli.command("run-collect-templates-data")
    def _run() -> None:
        """
        how to test locally:
        .venv/Scripts/activate
        flask --app src/app1.py run-collect-templates-data
        """
        start_job_cli(
            user={"username": "Background job"},
            job_type="collect_templates_data",
            args={"update_all":"true"},
            app=app,
        )

    @app.cli.command("collect-templates")
    def _run_not_update() -> None:
        """
        how to test locally:
        .venv/Scripts/activate
        flask --app src/app1.py collect-templates
        """
        start_job_cli(
            user={"username": "Background job"},
            job_type="collect_templates_data",
            args={"update_all":"false"},
            app=app,
        )
