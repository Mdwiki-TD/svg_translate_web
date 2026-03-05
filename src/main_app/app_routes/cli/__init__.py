"""CLI commands for SVG Translate Web."""

from __future__ import annotations

import click
from flask import Blueprint

from ...jobs_workers import jobs_worker

bp_cli = Blueprint("cli", __name__)


@bp_cli.cli.command("collect-main-files")
def collect_main_files() -> None:
    """Run collect_main_files job (for cron scheduling)."""
    click.echo("Starting collect_main_files job...")

    # Start the job without user auth (read-only operation)
    job_id = jobs_worker.start_job(user=None, job_type="collect_main_files")
    click.echo(f"Job {job_id} started")


__all__ = [
    "bp_cli",
]
