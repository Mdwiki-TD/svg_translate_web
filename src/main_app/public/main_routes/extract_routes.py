from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ...api_services import FilesService
from ...services.copysvg_wrapper import (
    ExtractResult,
    extract_from_path,
)

logger = logging.getLogger(__name__)

# Session key for preserving filename across OAuth redirect for extract
EXTRACT_FILENAME_KEY = "extract_filename"


class ExtractRoutes:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self.files_service = FilesService()
        self._setup_routes()

    def _setup_routes(self) -> None:
        routes = [
            ("/", "GET", self.dashboard),
            ("/<string:file_name>", "GET", self.extract_get),
            ("/", "POST", self.extract_post),
        ]
        for rule, method, target in routes:
            self.bp.route(rule, methods=[method])(target)

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


__all__ = [
    "ExtractRoutes",
]
