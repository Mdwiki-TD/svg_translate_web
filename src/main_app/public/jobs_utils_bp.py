"""Public routes for jobs utils."""

from __future__ import annotations

import logging
from pathlib import Path

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    send_from_directory,
    url_for,
)
from flask.typing import ResponseReturnValue
from werkzeug.wrappers.response import Response

from ..admin.decorators import admin_required
from ..config import settings
from ..jobs_workers.admin_jobs_workers.download_main_files.runner import create_main_files_zip

logger = logging.getLogger(__name__)


class UtilsJobsBp:
    """Jobs utils routes."""

    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self._setup_download_main_files_routes()
        self._setup_crop_main_files_routes()

    def _setup_download_main_files_routes(self) -> None:
        # ================================
        # download_main_files routes
        # ================================

        @self.bp.route("/download_main_files/file/<string:filename>", methods=["GET"])
        @admin_required
        def serve_download_main_file(filename: str) -> Response:
            """
            Serve a downloaded main file from the main_files_path directory.
            """
            response = send_from_directory(settings.paths.main_files_path, filename)
            response.headers["Content-Security-Policy"] = "script-src 'none'; object-src 'none'"
            response.headers["X-Content-Type-Options"] = "nosniff"
            return response

        @self.bp.route("/download_main_files/download-all", methods=["GET"])
        @admin_required
        def download_all_main_files() -> ResponseReturnValue:
            """Download all main files as a zip archive."""

            response, status_code = create_main_files_zip()

            # If the response is an error message (not a file), flash it and redirect
            if status_code != 200:
                flash(response, "warning" if status_code == 404 else "danger")
                return redirect(url_for("adminpanel.jobs.jobs_list", job_type="download_main_files"))

            return response

    def _setup_crop_main_files_routes(self) -> None:
        # ================================
        # crop-main-files routes
        # ================================

        @self.bp.route("/crop-main-files/original/<string:filename>", methods=["GET"])
        @admin_required
        def serve_crop_original_file(filename: str) -> Response:
            """
            Serve an original file from the crop_main_files_path/original directory.
            """
            filename = filename.removeprefix("File:")
            response = send_from_directory(Path(settings.paths.crop_main_files_path) / "original", filename)
            response.headers["Content-Security-Policy"] = "script-src 'none'; object-src 'none'"
            response.headers["X-Content-Type-Options"] = "nosniff"
            return response

        @self.bp.route("/crop-main-files/cropped/<string:filename>", methods=["GET"])
        @admin_required
        def serve_crop_cropped_file(filename: str) -> Response:
            """
            Serve a cropped file from the crop_main_files_path/cropped directory.
            """
            filename = filename.removeprefix("File:")
            response = send_from_directory(Path(settings.paths.crop_main_files_path) / "cropped", filename)
            response.headers["Content-Security-Policy"] = "script-src 'none'; object-src 'none'"
            response.headers["X-Content-Type-Options"] = "nosniff"
            return response

        @self.bp.route("/crop-main-files/compare/<string:original>/<string:cropped>", methods=["GET"])
        @admin_required
        def compare_crop_files(original: str, cropped: str) -> ResponseReturnValue:
            """Compare crop files"""

            original = original.removeprefix("File:")
            cropped = cropped.removeprefix("File:")
            return render_template(
                "admins/compare_crop_files.html",
                file_original=original,
                file_cropped=cropped,
            )


__all__ = [
    "UtilsJobsBp",
]
