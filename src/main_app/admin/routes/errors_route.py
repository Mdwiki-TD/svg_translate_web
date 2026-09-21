"""
Admin-only routes for checking errors.
"""

from __future__ import annotations

import logging
from pathlib import Path

from flask import Blueprint, flash, render_template, request
from flask.views import MethodView

from ...config import app_settings
from ..decorators import admin_required

logger = logging.getLogger(__name__)


def get_log_dir() -> Path:
    """Return configured log directory path."""
    return Path(app_settings.paths.log_dir)


class ErrorDashboardView(MethodView):
    """View to display log files and render selected file content."""

    decorators = [admin_required]

    @staticmethod
    def _list_log_files(log_dir: Path) -> list[str]:
        """List all .log files in the specified directory."""
        if not log_dir.is_dir():
            return []
        return sorted(f.name for f in log_dir.iterdir() if f.is_file() and f.suffix == ".log")

    @staticmethod
    def _read_text(error_file: Path) -> str:
        """Safely read content of a log file."""
        if not error_file.exists():
            logger.info("File not found: %s", error_file)
            return "No error log found."

        try:
            text = error_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            logger.exception("Error reading error log: %s", error_file)
            text = ""

        logger.info("File content length: %s bytes", f"{len(text):,}")
        return text

    def get(self, file_name: str | None = None) -> str:
        """Render log viewer dashboard with selected or requested log file."""
        selected_file = file_name or request.args.get("log_file", "errors.log")

        logger.info("Read file: %s", selected_file)

        logs_dir = get_log_dir()
        files = self._list_log_files(logs_dir)

        if selected_file not in files:
            flash(f"File {selected_file} not found")
            selected_file = "errors.log"
            logger.info("Changed file to: %s", selected_file)

        error_file = logs_dir / selected_file
        file_content = self._read_text(error_file)

        return render_template(
            "admins/errors.html",
            files=files,
            selected_file=selected_file,
            file_content=file_content,
        )


class CheckErrorsView:
    """Registrar class to bind error checking MethodViews to a Blueprint."""

    @staticmethod
    def register(bp: Blueprint) -> None:
        """Register error checking URL rules on the provided blueprint."""
        view = ErrorDashboardView.as_view("dashboard")

        # Primary route handling optional log filename parameter
        bp.add_url_rule("/", defaults={"file_name": None}, view_func=view)
        bp.add_url_rule("/<string:file_name>", view_func=view)


__all__ = [
    "ErrorDashboardView",
    "CheckErrorsView",
]
