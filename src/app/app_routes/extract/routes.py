import json
import logging
import shutil
import tempfile
from pathlib import Path

from CopySVGTranslation import extract
from flask import Blueprint, flash, render_template, request, session

from ...tasks.downloads.download import download_one_file

bp_extract = Blueprint("extract", __name__, url_prefix="/extract")
logger = logging.getLogger("svg_translate")

# Session key for preserving filename across OAuth redirect for extract
EXTRACT_FILENAME_KEY = "extract_filename"


@bp_extract.route("/", methods=["GET"])
def extract_translations():
    """Display form to extract translations from an SVG file."""
    # Restore filename from session if available (e.g., after OAuth redirect)
    filename = session.pop(EXTRACT_FILENAME_KEY, "")
    return render_template("extract/form.html", filename=filename)


@bp_extract.route("/", methods=["POST"])
def extract_translations_post():
    """Process SVG file and extract translations."""
    filename = request.form.get("filename", "").strip()

    # Remove "File:" prefix if present (keep original for display)
    original_filename = filename
    if filename.lower().startswith("file:"):
        filename = filename[5:].lstrip()

    if not filename:
        flash("Please provide a file name", "danger")
        return render_template("extract/form.html", filename=original_filename)

    logger.info(f"Starting extract translations for file: {filename}")

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
        except Exception as e:
            logger.error(f"Error extracting translations: {e}", exc_info=True)
            flash(f"Error extracting translations: {str(e)}", "danger")
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
        languages = sorted({lang for entry in translations.get("new", {}).values() if isinstance(entry, dict) for lang in entry})
        logger.info(f"Extracted languages: {len(languages):,}")

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
