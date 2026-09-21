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
from flask.views import MethodView
from flask.wrappers import Response

from ..admin.decorators import admin_required
from ..config import app_settings
from ..jobs_workers.admin_jobs_workers.download_main_files.zip_utils import create_main_files_zip

logger = logging.getLogger(__name__)


class ServeDownloadMainFileView(MethodView):
    """View to serve a downloaded main file from the main_files_path directory."""

    decorators = [admin_required]

    def get(self, filename: str) -> Response:
        """Serve a downloaded main file from the main_files_path directory."""
        response = send_from_directory(app_settings.paths.main_files_path, filename)
        response.headers["Content-Security-Policy"] = "script-src 'none'; object-src 'none'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response


class DownloadAllMainFilesView(MethodView):
    """View to download all main files as a zip archive."""

    decorators = [admin_required]

    def get(self) -> ResponseReturnValue:
        """Download all main files as a zip archive."""
        response, status_code = create_main_files_zip()

        # If the response is an error message (not a file), flash it and redirect
        if status_code != 200:
            flash(response, "warning" if status_code == 404 else "danger")
            return redirect(url_for("adminpanel.jobs.jobs_list", job_type="download_main_files"))

        return response


class ServeCropOriginalFileView(MethodView):
    """View to serve an original file from the crop_main_files_path/original directory."""

    decorators = [admin_required]

    def get(self, filename: str) -> Response:
        """Serve an original file from the crop_main_files_path/original directory."""
        filename = filename.removeprefix("File:")
        response = send_from_directory(Path(app_settings.paths.crop_main_files_path) / "original", filename)
        response.headers["Content-Security-Policy"] = "script-src 'none'; object-src 'none'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response


class ServeCropCroppedFileView(MethodView):
    """View to serve a cropped file from the crop_main_files_path/cropped directory."""

    decorators = [admin_required]

    def get(self, filename: str) -> Response:
        """Serve a cropped file from the crop_main_files_path/cropped directory."""
        filename = filename.removeprefix("File:")
        response = send_from_directory(Path(app_settings.paths.crop_main_files_path) / "cropped", filename)
        response.headers["Content-Security-Policy"] = "script-src 'none'; object-src 'none'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response


class CompareCropFilesView(MethodView):
    """View to compare original and cropped files side by side."""

    decorators = [admin_required]

    def get(self, original: str, cropped: str) -> ResponseReturnValue:
        """Compare crop files."""
        original = original.removeprefix("File:")
        cropped = cropped.removeprefix("File:")
        return render_template(
            "admins/compare_crop_files.html",
            file_original=original,
            file_cropped=cropped,
        )


class UtilsJobsBpRoutes:
    """Registrar class to bind jobs utils MethodViews to a Blueprint."""

    def register(self, bp: Blueprint) -> None:
        """Register jobs utils URL rules on the provided blueprint with admin protection."""
        bp.add_url_rule(
            "/download_main_files/file/<string:filename>",
            view_func=ServeDownloadMainFileView.as_view("serve_download_main_file"),
        )
        bp.add_url_rule(
            "/download_main_files/download-all",
            view_func=DownloadAllMainFilesView.as_view("download_all_main_files"),
        )
        bp.add_url_rule(
            "/crop-main-files/original/<string:filename>",
            view_func=ServeCropOriginalFileView.as_view("serve_crop_original_file"),
        )
        bp.add_url_rule(
            "/crop-main-files/cropped/<string:filename>",
            view_func=ServeCropCroppedFileView.as_view("serve_crop_cropped_file"),
        )
        bp.add_url_rule(
            "/crop-main-files/compare/<string:original>/<string:cropped>",
            view_func=CompareCropFilesView.as_view("compare_crop_files"),
        )


__all__ = [
    "UtilsJobsBpRoutes",
]
