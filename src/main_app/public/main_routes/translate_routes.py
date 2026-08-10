"""Interactive translate workflow: pick a file, pick a language, edit rows, inject, download/upload."""

from __future__ import annotations

import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from ...api_services import FilesService, get_user_site
from ...api_services.files_service import UploadService
from ...config import settings
from ...shared.copysvg_wrapper import (
    ExtractResult,
    cleanup_old_sessions,
    extract_from_path,
    inject_step_one_file,
    mapping_from_rows,
    rows_for_language,
    summary_from_rows,
)
from ...shared.copysvg_wrapper.mapping import ExtractorData
from ...shared.copysvg_wrapper.translate_session import TranslateSession
from ..auth.utils import load_user, oauth_required

logger = logging.getLogger(__name__)

# Maximum upload size for SVG files (5 MB)
_MAX_UPLOAD_BYTES = 5 * 1024 * 1024


def _sessions_base_dir() -> Path:
    """Return the base directory for translate sessions."""
    return Path(settings.paths.svg_data)


class TranslateRoutes:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self.files_service = FilesService()
        self._setup_routes()

    def _setup_routes(self) -> None:
        self.bp.route("/", methods=["GET"])(self.select_form)
        self.bp.route("/", methods=["POST"])(self.select_post)
        self.bp.route("/upload", methods=["POST"])(self.upload_post)
        self.bp.route("/<string:session_id>", methods=["GET"])(self.edit_form)
        self.bp.route("/<string:session_id>", methods=["POST"])(self.commit_post)
        self.bp.route("/<string:session_id>/download", methods=["GET"])(self.download_get)
        self.bp.route("/<string:session_id>/upload", methods=["POST"])(self.upload_commons_post)
        self.bp.route("/<string:session_id>/result", methods=["GET"])(self.result_page)

    # ------------------------------------------------------------------
    # Select file + language
    # ------------------------------------------------------------------

    def select_form(self) -> str:
        """Show the file/language selection form."""
        # Periodically clean up old sessions
        cleanup_old_sessions(_sessions_base_dir(), max_age_hours=24)
        return render_template("translate/select.html")

    def select_post(self) -> str:
        """Handle Commons filename submission: fetch, extract, create session."""
        filename = request.form.get("filename", "").strip()
        lang = request.form.get("lang", "").strip()

        if not filename:
            flash("Please provide a file name", "danger")
            return render_template("translate/select.html")

        if not lang:
            flash("Please select a target language", "danger")
            return render_template("translate/select.html", filename=filename)

        # Normalize
        clean_name = filename.removeprefix("File:").strip()
        if not clean_name or clean_name != Path(clean_name).name or clean_name in {".", ".."}:
            flash(f"Invalid file name: {filename}", "danger")
            return render_template("translate/select.html", filename=filename)

        # Check file exists on Commons
        file_info = self.files_service.get_file_info(f"File:{clean_name}")
        if not file_info.exists:
            flash(f"File:{clean_name} does not exist on Commons", "danger")
            return render_template("translate/select.html", filename=filename)

        # Download + extract
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_dir = Path(tmp_dir)
            download_result = self.files_service.download_and_save(
                title=clean_name,
                out_dir=temp_dir,
                overwrite_download=True,
            )
            if download_result.result != "success" or not download_result.path:
                flash(f"Failed to download file: {clean_name}", "danger")
                return render_template("translate/select.html", filename=filename)

            extract_result: ExtractResult = extract_from_path(
                Path(download_result.path), fast_return_false=False
            )

            if not extract_result.success or extract_result.mapping is None:
                error_msg = extract_result.error or "No translatable text found in this file."
                flash(f"Cannot use this file: {error_msg}", "danger")
                return render_template("translate/select.html", filename=filename)

            mapping = extract_result.mapping
            if mapping.is_empty():
                flash("No translatable text found in this SVG file.", "warning")
                return render_template("translate/select.html", filename=filename)

            # Create session
            session_obj = TranslateSession.create(
                source_type="commons",
                commons_title=f"File:{clean_name}",
                mapping=mapping,
                created_at=datetime.now(timezone.utc).isoformat(),
            )

            base_dir = _sessions_base_dir()
            session_dir = session_obj.session_dir(base_dir)
            session_dir.mkdir(parents=True, exist_ok=True)

            # Cache the SVG in session directory
            src_path = Path(download_result.path)
            dst_path = session_obj.svg_path(base_dir)
            shutil.copy2(str(src_path), str(dst_path))

            session_obj.save(base_dir)

            logger.info(
                "Translate session created: %s for %s (lang=%s)",
                session_obj.session_id,
                clean_name,
                lang,
            )

            return redirect(url_for("translate.edit_form", session_id=session_obj.session_id, lang=lang))

    def upload_post(self) -> str:
        """Handle direct SVG file upload: extract, create session."""
        uploaded = request.files.get("svg_file")
        lang = request.form.get("lang", "").strip()

        if not uploaded or not uploaded.filename:
            flash("Please select an SVG file to upload", "danger")
            return render_template("translate/select.html")

        if not lang:
            flash("Please select a target language", "danger")
            return render_template("translate/select.html")

        # Validate file
        if not uploaded.filename.lower().endswith(".svg"):
            flash("Only SVG files are accepted", "danger")
            return render_template("translate/select.html")

        # Read and validate size
        data = uploaded.read()
        if len(data) > _MAX_UPLOAD_BYTES:
            flash(f"File too large. Maximum size is {_MAX_UPLOAD_BYTES // (1024 * 1024)} MB.", "danger")
            return render_template("translate/select.html")

        # Save to temp, extract
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_dir = Path(tmp_dir)
            safe_filename = Path(uploaded.filename).name
            temp_file = temp_dir / safe_filename
            temp_file.write_bytes(data)

            extract_result: ExtractResult = extract_from_path(temp_file, fast_return_false=False)

            if not extract_result.success or extract_result.mapping is None:
                error_msg = extract_result.error or "No translatable text found in this file."
                flash(f"Cannot use this file: {error_msg}", "danger")
                return render_template("translate/select.html")

            mapping = extract_result.mapping
            if mapping.is_empty():
                flash("No translatable text found in this SVG file.", "warning")
                return render_template("translate/select.html")

            # Create session
            session_obj = TranslateSession.create(
                source_type="upload",
                upload_filename=uploaded.filename,
                mapping=mapping,
                created_at=datetime.now(timezone.utc).isoformat(),
            )

            base_dir = _sessions_base_dir()
            session_dir = session_obj.session_dir(base_dir)
            session_dir.mkdir(parents=True, exist_ok=True)

            # Cache the SVG in session directory
            dst_path = session_obj.svg_path(base_dir)
            dst_path.write_bytes(data)

            session_obj.save(base_dir)

            logger.info(
                "Translate session created from upload: %s (%s, lang=%s)",
                session_obj.session_id,
                uploaded.filename,
                lang,
            )

            return redirect(url_for("translate.edit_form", session_id=session_obj.session_id, lang=lang))

    # ------------------------------------------------------------------
    # Edit form
    # ------------------------------------------------------------------

    def edit_form(self, session_id: str) -> str:
        """Show the translation edit table for a session + language."""
        lang = request.args.get("lang", "").strip()

        base_dir = _sessions_base_dir()
        session_obj = TranslateSession.load(session_id, base_dir)
        if session_obj is None:
            flash("Session expired or not found. Please start again.", "warning")
            return redirect(url_for("translate.select_form"))

        if not lang:
            # Default to first missing language, or first available
            mapping = session_obj.get_mapping()
            all_langs = sorted(mapping.all_languages())
            lang = all_langs[0] if all_langs else "en"

        mapping = session_obj.get_mapping()
        rows = rows_for_language(mapping, lang)
        summary = summary_from_rows(rows)
        all_langs = sorted(mapping.all_languages())

        display_title = session_obj.commons_title or session_obj.upload_filename or "Uploaded SVG"

        return render_template(
            "translate/edit.html",
            session_id=session_id,
            lang=lang,
            rows=[r.to_dict() for r in rows],
            summary=summary,
            display_title=display_title,
            all_languages=all_langs,
        )

    # ------------------------------------------------------------------
    # Commit (inject + result)
    # ------------------------------------------------------------------

    def commit_post(self, session_id: str) -> str:
        """Process form submission: build mapping, inject, show result."""
        lang = request.form.get("lang", "").strip()

        base_dir = _sessions_base_dir()
        session_obj = TranslateSession.load(session_id, base_dir)
        if session_obj is None:
            flash("Session expired or not found. Please start again.", "warning")
            return redirect(url_for("translate.select_form"))

        if not lang:
            flash("No language specified", "danger")
            return redirect(url_for("translate.edit_form", session_id=session_id))

        # Collect form rows by finding all source_N keys
        form_rows: list[dict[str, str]] = []
        source_keys = [k for k in request.form.keys() if k.startswith("source_")]
        for source_key in sorted(source_keys, key=lambda k: int(k.split("_")[1])):
            idx = source_key.split("_")[1]
            target_key = f"target_{idx}"
            source_val = request.form.get(source_key)
            target_val = request.form.get(target_key)
            if source_val is not None:
                form_rows.append({"source": source_val, "target": target_val or ""})

        user_mapping = mapping_from_rows(form_rows, lang)

        if not user_mapping.get("new"):
            flash("No translations were provided. Nothing to inject.", "warning")
            return redirect(url_for("translate.edit_form", session_id=session_id, lang=lang))

        # Inject into cached SVG
        svg_path = session_obj.svg_path(base_dir)
        output_path = session_obj.output_path(base_dir)

        inject_result = inject_step_one_file(
            file_path=svg_path,
            translations=user_mapping,
            output_file=output_path,
            overwrite_translations=True,
        )

        display_title = session_obj.commons_title or session_obj.upload_filename or "Uploaded SVG"

        if inject_result.result is False:
            flash(f"Injection failed: {inject_result.msg}", "danger")
            return redirect(url_for("translate.edit_form", session_id=session_id, lang=lang))

        # Build stats for result display
        stats: dict[str, Any] = {
            "result": inject_result.result,
            "msg": inject_result.msg,
            "new_languages_count": inject_result.new_languages_count,
            "updated_translations": inject_result.updated_translations,
            "inserted_translations": inject_result.inserted_translations,
        }

        flash(f"Translations applied: {inject_result.msg}", "success")

        return render_template(
            "translate/result.html",
            session_id=session_id,
            lang=lang,
            stats=stats,
            display_title=display_title,
            is_commons=session_obj.source_type == "commons",
        )

    # ------------------------------------------------------------------
    # Download result SVG
    # ------------------------------------------------------------------

    def download_get(self, session_id: str) -> Any:
        """Download the injected SVG file."""

        base_dir = _sessions_base_dir()
        session_obj = TranslateSession.load(session_id, base_dir)
        if session_obj is None:
            flash("Session expired or not found.", "warning")
            return redirect(url_for("translate.select_form"))

        output_path = session_obj.output_path(base_dir)
        if not output_path.exists():
            flash("No output file available. Please run the injection first.", "warning")
            return redirect(url_for("translate.edit_form", session_id=session_id))

        # Build a download filename
        if session_obj.source_type == "commons":
            download_name = (session_obj.commons_title or "").removeprefix("File:")
            if not download_name:
                download_name = "translated.svg"
        else:
            download_name = session_obj.upload_filename or "translated.svg"

        if not download_name.lower().endswith(".svg"):
            download_name += ".svg"

        return send_file(
            str(output_path),
            mimetype="image/svg+xml",
            as_attachment=True,
            download_name=download_name,
        )

    # ------------------------------------------------------------------
    # Upload to Commons (requires OAuth)
    # ------------------------------------------------------------------

    @oauth_required
    def upload_commons_post(self, session_id: str) -> str:
        """Upload the injected SVG back to Commons (replaces existing file)."""

        base_dir = _sessions_base_dir()
        session_obj = TranslateSession.load(session_id, base_dir)
        if session_obj is None:
            flash("Session expired or not found.", "warning")
            return redirect(url_for("translate.select_form"))

        if session_obj.source_type != "commons":
            flash("Upload to Commons is only available for files sourced from Commons.", "danger")
            return redirect(url_for("translate.edit_form", session_id=session_id))

        output_path = session_obj.output_path(base_dir)
        if not output_path.exists():
            flash("No output file available. Please run the injection first.", "warning")
            return redirect(url_for("translate.edit_form", session_id=session_id))

        # Get user site for upload
        user = load_user()
        if not user:
            flash("Authentication required for upload.", "danger")
            return redirect(url_for("translate.edit_form", session_id=session_id))

        site = get_user_site(user.to_auth_payload())
        if not site:
            flash("Failed to establish Commons session. Please log in again.", "danger")
            return redirect(url_for("translate.edit_form", session_id=session_id))

        # Determine filename
        commons_title = session_obj.commons_title  # e.g. "File:Example.svg"
        filename = commons_title.removeprefix("File:")

        lang = request.form.get("lang", "unknown")
        # Basic validation for language code
        if not lang or len(lang) > 20 or not lang.replace('-', '').isalpha():
            lang = "unknown"
        summary = f"/* SVG translation */ Added/updated {lang} translations via Copy SVG Translations tool"

        upload_service = UploadService(site)
        upload_result = upload_service.upload_svg(
            filename=filename,
            file_path=output_path,
            summary=summary,
        )

        if upload_result.ok:
            flash(f"Successfully uploaded to Commons: {commons_title}", "success")
            logger.info("Uploaded translated SVG to Commons: %s (session=%s)", commons_title, session_id)
        elif upload_result.ok is None:
            flash(f"Upload skipped: {upload_result.msg or 'no changes detected'}", "info")
        else:
            flash(f"Upload failed: {upload_result.error}", "danger")
            logger.error(
                "Upload failed for %s: %s (%s)",
                commons_title,
                upload_result.error,
                upload_result.error_details,
            )

        return redirect(
            url_for(
                "translate.result_page",
                session_id=session_id,
                lang=lang,
            )
        )

    # ------------------------------------------------------------------
    # Result page (shown after commit or upload)
    # ------------------------------------------------------------------

    def result_page(self, session_id: str) -> str:
        """Show the result page after commit/upload."""
        lang = request.args.get("lang", "")

        base_dir = _sessions_base_dir()
        session_obj = TranslateSession.load(session_id, base_dir)
        if session_obj is None:
            flash("Session expired or not found.", "warning")
            return redirect(url_for("translate.select_form"))

        display_title = session_obj.commons_title or session_obj.upload_filename or "Uploaded SVG"
        output_path = session_obj.output_path(base_dir)

        return render_template(
            "translate/result.html",
            session_id=session_id,
            lang=lang,
            stats={},
            display_title=display_title,
            is_commons=session_obj.source_type == "commons",
            output_exists=output_path.exists(),
        )


__all__ = [
    "TranslateRoutes",
]
