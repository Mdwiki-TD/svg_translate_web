""" """

from __future__ import annotations

import click
from flask import Flask
from flask.cli import AppGroup

from ..database.services.data import DETAIL_RETENTION_DAYS
from ..database.services.error_log_service import BackfillAlreadyDoneError, ErrorLogService


def register_error_log_commands(app: Flask) -> None:
    """
    Register ``flask error-logs`` maintenance commands.

    Weekly cron example:
        0 3 * * 0  cd /path/to/app && flask error-logs purge
    """
    group = AppGroup("error-logs", help="Maintain the error_logs and error_log_daily tables.")

    @group.command("purge")
    @click.option("--days", default=DETAIL_RETENTION_DAYS, show_default=True, type=int)
    @click.option("--batch", default=5000, show_default=True, type=int)
    def purge_command(days: int, batch: int) -> None:
        """Delete detailed rows older than DAYS (daily counters are kept)."""
        deleted = ErrorLogService().purge_older_than(days=days, batch=batch)
        click.echo(f"Deleted {deleted} rows from error_logs older than {days} days")

    @group.command("backfill")
    @click.option(
        "--before",
        required=True,
        type=click.DateTime(),
        help="Deploy time of the new logging code (UTC); only older rows are aggregated.",
    )
    def backfill_command(before) -> None:
        """
        One-time: aggregate existing error_logs rows into error_log_daily (refuses to run twice).
        flask --app "$HOME/www/python/src/app.py" error-logs backfill --before "2026-11-18 20:32:12"
        """
        try:
            affected = ErrorLogService().backfill_daily(before)
        except BackfillAlreadyDoneError as exc:
            # Non-zero exit code, nothing was written
            raise click.ClickException(str(exc)) from exc
        click.echo(f"Backfill finished (rows affected: {affected})")

    app.cli.add_command(group)


__all__ = [
    "register_error_log_commands",
]
