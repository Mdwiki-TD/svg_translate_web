from __future__ import annotations

import json
import logging
import shutil
import tempfile
from pathlib import Path

from CopySVGTranslation import extract  # type: ignore
from flask import Blueprint, flash, render_template, request, session

from ...api_services.files_service import download_one_file

logger = logging.getLogger(__name__)

# Session key for preserving filename across OAuth redirect for extract
EXTRACT_FILENAME_KEY = "extract_filename"


class ExtractRoutes:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.bp.route("/", methods=["GET"])
        def extract_translations() -> str:
            """Display form to extract translations from an SVG file."""
            # Restore filename from session if available (e.g., after OAuth redirect)
            filename = session.pop(EXTRACT_FILENAME_KEY, "")
            return render_template("extract/form.html", filename=filename)

        @self.bp.route("/", methods=["POST"])
        def extract_translations_post() -> str:
            """Process SVG file and extract translations."""
            filename = request.form.get("filename", "").strip()

            # Remove "File:" prefix if present (keep original for display)
            original_filename = filename
            if filename.lower().startswith("file:"):
                filename = filename[5:].lstrip()
            original_filename = f"File:{filename}"

            if not filename:
                flash("Please provide a file name", "danger")
                return render_template("extract/form.html", filename=original_filename)

            logger.info("Starting extract translations for file: %s", filename)

            # Create temporary directory for download
            temp_dir = Path(tempfile.mkdtemp())
            try:
                # Download the file
                result = download_one_file(title=filename, out_dir=temp_dir, i=0, overwrite=True)

                if result.get("result") != "success" or not result.get("path"):
                    flash(f"Failed to download file: {filename}", "danger")
                    return render_template("extract/form.html", filename=original_filename)

                file_path = Path(result["path"])

                # Extract translations using CopySVGTranslation
                try:
                    translations = extract(svg_file_path=file_path, case_insensitive=True)
                    if not isinstance(translations, dict):
                        flash("Invalid or empty translation data", "danger")
                        return render_template("extract/form.html", filename=original_filename)

                except Exception as e:
                    logger.error("Error extracting translations: %s", e, exc_info=True)
                    flash("An error occurred while extracting translations", "danger")
                    return render_template("extract/form.html", filename=original_filename)

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
                languages = sorted(
                    {lang for entry in translations.get("new", {}).values() if isinstance(entry, dict) for lang in entry}
                )
                logger.info("Extracted languages: %s", len(languages))

                # Convert translations to pretty JSON for display
                translations_json = json.dumps(translations, ensure_ascii=False, indent=4)

                flash("Translations extracted successfully", "success")
                return render_template(
                    "extract/result.html",
                    filename=original_filename,
                    languages=languages,
                    translations_json=translations_json,
                    translations=translations,
                )

            finally:
                # Clean up temporary directory
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)


__all__ = [
    "ExtractRoutes",
]
