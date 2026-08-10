from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ...api_services.files_service import get_file_info
from ...api_services.files_service.download_file_utils import download_one_file
from ...shared.copysvg_wrapper import (
    ExtractResult,
    extract_from_path,
)

logger = logging.getLogger(__name__)

# Session key for preserving filename across OAuth redirect for extract
EXTRACT_FILENAME_KEY = "extract_filename"


def work_file(filename: str) -> ExtractResult | None:

    logger.info("Starting extract translations for file: %s", filename)

    # Reject invalid filesystem filenames before calling download_one_file()
    if not filename or filename != Path(filename).name or filename in {".", ".."}:
        flash(f"Invalid file name: {filename}", "danger")
        return None

    # Create temporary directory for download
    temp_dir = Path(tempfile.mkdtemp())
    try:
        # Download the file
        result = download_one_file(title=filename, out_dir=temp_dir, overwrite_download=True)

        if result.get("result") != "success" or not result.get("path"):
            flash(f"Failed to download file: {filename}", "danger")
            return None

        file_path = Path(result["path"])

        extract_result: ExtractResult = extract_from_path(file_path, fast_return_false=False)

        return extract_result

    finally:
        # Clean up temporary directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


class ExtractRoutes:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self._setup_routes()

    def _setup_routes(self) -> None:
        self.bp.route("/", methods=["GET"])(self.dashboard)
        self.bp.route("/<string:file_name>", methods=["GET"])(self.extract_get)
        self.bp.route("/", methods=["POST"])(self.extract_post)

    def extract_post(self) -> str:
        filename = request.form.get("filename", "").strip()
        if not filename:
            flash("Please provide a file name", "danger")
            return render_template("extract/form.html", filename=filename)

        # redirect to extract_get to update browser URL
        return redirect(url_for("extract.extract_get", file_name=filename))

    def extract_get(self, file_name: str) -> str:
        return self.show_result(file_name.strip())

    def dashboard(self) -> str:
        """Display form to extract translations from an SVG file."""
        # Restore filename from session if available (e.g., after OAuth redirect)
        filename = session.pop(EXTRACT_FILENAME_KEY, "")
        return render_template("extract/form.html", filename=filename)

    def show_result(self, filename: str) -> str:
        """Process SVG file and extract translations."""
        filename = str(filename).strip()

        # Remove "File:" prefix if present (keep original for display)
        if filename.lower().startswith("file:"):
            filename = filename[5:].lstrip()

        if not filename.strip():
            flash("Please provide a file name", "danger")
            return render_template("extract/form.html", filename=filename)

        prefixed_file_name = f"File:{filename}"

        file_info = get_file_info(prefixed_file_name)
        if not file_info.exists:
            flash(f"File {prefixed_file_name} not exists", "danger")
            logger.error(file_info.to_dict())
            return render_template("extract/form.html", filename=prefixed_file_name)

        # ========================
        result = work_file(filename)
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


__all__ = [
    "ExtractRoutes",
]
