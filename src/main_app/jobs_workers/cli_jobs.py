"""Base worker infrastructure with standardized lifecycle management."""

from __future__ import annotations

import logging

from flask import Flask

from .jobs_worker import start_job_cli

logger = logging.getLogger(__name__)

def register_cli_jobs(app: Flask) -> None:
    @app.cli.command("run-collect-templates-data")
    def _run() -> None:
        start_job_cli(
            user={"username": "Background job"},
            job_type="collect_templates_data",
            app=app,
        )
