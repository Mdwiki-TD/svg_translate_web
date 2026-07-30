"""
Admin-only routes for checking errors.
"""

from __future__ import annotations
import logging

from pathlib import Path

from flask import Blueprint, render_template, flash, request

from ...config import settings
from ..decorators import admin_required

logger = logging.getLogger(__name__)

def get_log_dir() -> Path:
    return Path(settings.paths.log_dir)

class CheckErrorsRoutes:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self._setup_routes()

    def _setup_routes(self) -> None:
        self.bp.route("/", methods=["GET"])(admin_required(self.dashboard))
        self.bp.route("/<string:file_name>", methods=["GET"])(admin_required(self.app_log))

    @staticmethod
    def _list_log_files(log_dir: Path) -> list[str]:
        if not log_dir.is_dir():
            return []
        return sorted(f.name for f in log_dir.iterdir() if f.is_file() and f.suffix == ".log")

    def dashboard(self):
        file_name = request.args.get("log_file", "errors.log")
        return self.render_result(file_name)

    def app_log(self, file_name: str = ""):
        return self.render_result(file_name)

    def render_result(self, selected_file: str = "errors.log"):
        logger.info("Read file: %s", selected_file)

        logs_dir = get_log_dir()
        files = self._list_log_files(logs_dir)

        if selected_file not in files:
            flash(f"File {selected_file} not found")
            selected_file = "errors.log"
            logger.info("Changed file to: %s", selected_file)

        error_file = logs_dir / selected_file
        file_content = self.read_text(error_file)

        return render_template(
            "admins/errors.html",
            files=files,
            selected_file=selected_file,
            file_content=file_content,
        )

    def read_text(self, error_file: Path) -> str:

        if not error_file.exists():
            return "No error log found."

        try:
            text = error_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Error reading error log: {e}")
            text = ""
        return text

__all__ = [
    "CheckErrorsRoutes",
]
