"""Base worker infrastructure with standardized lifecycle management."""

from __future__ import annotations

import logging

from flask import Flask

from .jobs_worker import start_job

logger = logging.getLogger(__name__)

def register_cli_jobs(app: Flask) -> None:
    @app.cli.command("run-collect-templates-data")
    def _run() -> None:
        start_job(
            user={"username": "Background job"},
            job_type="collect_templates_data",
            args={"update_all":"true"},
            daemon=False,
        )
