from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask.views import MethodView

from ...api_services import FilesService
from ...services.copysvg_wrapper import (
    ExtractResult,
    extract_from_path,
)

logger = logging.getLogger(__name__)

# Session key for preserving filename across OAuth redirect for extract
EXTRACT_FILENAME_KEY = "extract_filename"


class ExtractDashboardView(MethodView):
    """View to handle the extract form dashboard and form submissions."""

    def get(self) -> str:
        """Display form to extract translations from an SVG file."""
        # Restore filename from session if available (e.g., after OAuth redirect)
        filename = session.pop(EXTRACT_FILENAME_KEY, "")
        return render_template("extract/form.html", filename=filename)

    def post(self) -> str:
        """Validate form input and redirect to the GET extract view."""
        filename = (request.form.get("filename", "") or request.form.get("file_name", "")).strip()
        if not filename:
            flash("Please provide a file name", "danger")
            return render_template("extract/form.html", filename=filename)

        # Redirect to extract_get to update browser URL
        return redirect(url_for("extract.extract_get", file_name=filename))


class ExtractProcessView(MethodView):
    """View to handle processing and extracting translations from an SVG file."""

    def __init__(self) -> None:
        self.files_service = FilesService()

    def get(self, file_name: str) -> str:
        """Process SVG file and extract translations."""
        filename = str(file_name).strip()

        # Remove "File:" prefix if present (keep original for display)
        if filename.lower().startswith("file:"):
            filename = filename[5:].lstrip()

        if not filename.strip():
            flash("Please provide a file name", "danger")
            return render_template("extract/form.html", filename=filename)

        prefixed_file_name = f"File:{filename}"

        file_info = self.files_service.get_file_info(prefixed_file_name)
        if not file_info.exists:
            flash(f"File {prefixed_file_name} not exists", "danger")
            logger.error(file_info.to_json())
            return render_template("extract/form.html", filename=prefixed_file_name)

        # ========================
        result = self.work_file(filename)
        mapping = result.mapping if result else None

        if result is None or mapping is None:
            flash("Invalid or empty translation data", "danger")
            return render_template(
                "extract/result.html",
                filename=prefixed_file_name,
                languages=[],
                translations={},
            )

        languages = mapping.all_languages()

        if not mapping.is_empty():
            flash("Translations extracted successfully", "success")
        else:
            flash("No translations found", "warning")

        logger.info("Extracted languages: %s", len(languages))

        return render_template(
            "extract/result.html",
            filename=prefixed_file_name,
            languages=languages,
            translations=mapping.to_json(),
        )

    def work_file(self, filename: str) -> ExtractResult | None:
        """Download file and perform translation extraction."""
        logger.info("Starting extract translations for file: %s", filename)

        # Reject invalid filesystem filenames before calling download_and_save()
        if not filename or filename != Path(filename).name or filename in {".", ".."}:
            flash(f"Invalid file name: {filename}", "danger")
            return None

        # Create temporary directory for download
        temp_dir = Path(tempfile.mkdtemp())
        try:
            # Download the file
            download_result = self.files_service.download_and_save(
                title=filename,
                out_dir=temp_dir,
                overwrite_download=True,
            )

            if download_result.result != "success" or not download_result.path:
                flash(f"Failed to download file: {filename}", "danger")
                return None

            file_path = Path(download_result.path)

            extract_result: ExtractResult = extract_from_path(file_path, fast_return_false=False)
            return extract_result

        finally:
            # Clean up temporary directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir)


class ExtractView:
    """Registrar class to bind extract MethodViews to a Blueprint."""

    @staticmethod
    def register(bp: Blueprint) -> None:
        """Register extract URL rules on the provided blueprint."""
        bp.add_url_rule("/", view_func=ExtractDashboardView.as_view("dashboard"))
        bp.add_url_rule("/<string:file_name>", view_func=ExtractProcessView.as_view("extract_get"))


__all__ = [
    "ExtractDashboardView",
    "ExtractProcessView",
    "ExtractView",
]
