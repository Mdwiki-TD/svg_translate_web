from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any

from CopySVGTranslation import extract  # type: ignore
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ...api_services.files_service import download_one_file, get_file_info

logger = logging.getLogger(__name__)

# Session key for preserving filename across OAuth redirect for extract
EXTRACT_FILENAME_KEY = "extract_filename"


def work_file(filename: str) -> dict[str, Any] | None:

    logger.info("Starting extract translations for file: %s", filename)

    # Reject invalid filesystem filenames before calling download_one_file()
    if not filename or filename != Path(filename).name or filename in {".", ".."}:
        flash(f"Invalid file name: {filename}", "danger")
        return None

    # Create temporary directory for download
    temp_dir = Path(tempfile.mkdtemp())
    try:
        # Download the file
        result = download_one_file(title=filename, out_dir=temp_dir, overwrite=True)

        if result.get("result") != "success" or not result.get("path"):
            flash(f"Failed to download file: {filename}", "danger")
            return None

        file_path = Path(result["path"])

        # Extract translations using CopySVGTranslation
        try:
            translations = extract(svg_file_path=file_path, case_insensitive=True)
            if not isinstance(translations, dict):
                flash("Invalid or empty translation data", "danger")
                return None

        except Exception as e:
            logger.error("Error extracting translations: %s", e, exc_info=True)
            flash("An error occurred while extracting translations", "danger")
            return None

        translations.pop("tspans_by_id", None)

        # {"new":"150": { "ar": "150", "ca": "150", "es": "150", "hr": "150", "pt": "150", "si": "150", "uk": "150", "id": "150" },}
        new_data = translations.get("new", {})

        # sort new_data by keys, but numbers at last
        translations["new"] = dict(
            sorted(
                new_data.items(),
                key=lambda item: (isinstance(item[0], str) and item[0].isdigit(), item[0]),
            )
        )
        return translations

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
        translations = work_file(filename)

        if translations is None:
            translations = {}
            languages: list[str] = []
        else:
            translations_new = translations.get("new", {})
            languages = []
            if translations_new:
                languages = sorted(
                    {lang for entry in translations["new"].values() if isinstance(entry, dict) for lang in entry}
                )
                flash("Translations extracted successfully", "success")
            else:
                flash("No translations found", "warning")


        logger.info("Extracted languages: %s", len(languages))

        return render_template(
            "extract/result.html",
            filename=prefixed_file_name,
            languages=languages,
            translations=translations,
        )


__all__ = [
    "ExtractRoutes",
]
