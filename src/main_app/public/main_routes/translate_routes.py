from __future__ import annotations

import json
import logging
import secrets
import shutil
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
from flask.views import MethodView

from ...api_services import FilesService, UploadService, get_user_site
from ...config import app_settings
from ...public.auth import oauth_required
from ...services.copysvg_wrapper import InjectResult, extract_from_path, inject_step_one_file
from ...services.copysvg_wrapper.mapping import TranslationMapping
from ..utils.routes_utils import load_auth_payload

logger = logging.getLogger(__name__)


def get_session_dir(session_id: str) -> Path:
    """Get the path to a session's directory and ensure it exists."""
    safe_session_id = "".join(c for c in session_id if c.isalnum())
    session_dir = Path(app_settings.paths.main_files_path) / "translate_sessions" / safe_session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


class TranslateDashboardView(MethodView):
    """View to handle the main translate selection form and submission."""

    decorators = [oauth_required]

    def __init__(self) -> None:
        self.files_service = FilesService()

    def get(self) -> str:
        """Display select form with filename and language fields."""
        return render_template("translate/form.html")

    def post(self) -> Any:
        """Process selection form and redirect to edit view with a unique session_id."""
        filename = (request.form.get("filename", "") or request.form.get("file_name", "")).strip()
        lang = request.form.get("lang", "").strip().lower()

        if not filename or not lang:
            flash("Please provide both file name and language code", "danger")
            return redirect(url_for("translate.dashboard"))

        processed_filename = filename
        if processed_filename.lower().startswith("file:"):
            processed_filename = processed_filename[5:].lstrip()

        prefixed_file_name = f"File:{processed_filename}"

        file_info = self.files_service.get_file_info(prefixed_file_name)
        if not file_info.exists:
            flash(f"File {prefixed_file_name} does not exist", "danger")
            return render_template("translate/form.html", filename=filename, lang=lang)

        # Download original once
        session_id = secrets.token_hex(16)
        session_dir = get_session_dir(session_id)

        download_result = self.files_service.download_and_save(
            title=processed_filename,
            out_dir=session_dir,
            overwrite_download=True,
        )
        if download_result.result != "success" or not download_result.path:
            flash(f"Failed to download file: {processed_filename}", "danger")
            return redirect(url_for("translate.dashboard"))

        # Rename the downloaded SVG to session.svg for standard naming
        downloaded_path = Path(download_result.path)
        svg_path = session_dir / "session.svg"
        if downloaded_path.exists() and downloaded_path != svg_path:
            downloaded_path.rename(svg_path)

        extract_result = extract_from_path(svg_path, fast_return_false=False)
        mapping = extract_result.mapping

        if extract_result is None or mapping is None or extract_result.error:
            flash(
                f"Failed to parse or extract translations from {processed_filename}: {extract_result.error or ''}",
                "danger",
            )
            if session_dir.exists():
                shutil.rmtree(session_dir)
            return redirect(url_for("translate.dashboard"))

        # Save session JSON
        session_data = {
            "filename": processed_filename,
            "lang": lang,
            "mapping": mapping.to_json(),
        }
        json_path = session_dir / "session.json"
        json_path.write_text(json.dumps(session_data, ensure_ascii=False, indent=2), encoding="utf-8")

        return redirect(url_for("translate.edit", session_id=session_id))


class TranslateEditView(MethodView):
    """View to display English text segments with parallel translation inputs for editing."""

    decorators = [oauth_required]

    def get(self) -> Any:
        """Render the translation editor page for the current session."""
        session_id = request.args.get("session_id", "").strip()
        if not session_id:
            flash("Missing session ID", "danger")
            return redirect(url_for("translate.dashboard"))

        session_dir = get_session_dir(session_id)
        json_path = session_dir / "session.json"
        svg_path = session_dir / "session.svg"

        if not json_path.exists() or not svg_path.exists():
            flash("Session expired or invalid", "danger")
            return redirect(url_for("translate.dashboard"))

        try:
            session_data = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            flash("Error loading translation session", "danger")
            return redirect(url_for("translate.dashboard"))

        filename = session_data.get("filename")
        lang = session_data.get("lang")
        mapping_data = session_data.get("mapping", {})

        # Extract only mapping['new'] keys for translating
        new_translations = mapping_data.get("new", {})
        all_keys = sorted(new_translations.keys())

        texts_with_translations = []
        for key in all_keys:
            existing_trans = ""
            if key in new_translations and lang in new_translations[key]:
                existing_trans = new_translations[key][lang]

            texts_with_translations.append(
                {
                    "original": key,
                    "translation": existing_trans,
                }
            )

        return render_template(
            "translate/edit.html",
            session_id=session_id,
            filename=f"File:{filename}",
            lang=lang,
            texts_with_translations=texts_with_translations,
        )


class TranslateSaveView(MethodView):
    """View to process translation injection and handle download or upload actions."""

    decorators = [oauth_required]

    def post(self) -> Any:
        """Inject translations into SVG and execute download or upload to Commons."""
        session_id = request.form.get("session_id", "").strip()
        action = request.form.get("action", "upload").strip()  # "upload" or "download"
        originals = request.form.getlist("originals")
        translations = request.form.getlist("translations")

        if not session_id:
            flash("Missing session ID", "danger")
            return redirect(url_for("translate.dashboard"))

        if len(originals) != len(translations):
            flash("Form submission error: field count mismatch", "danger")
            return redirect(url_for("translate.edit", session_id=session_id))

        session_dir = get_session_dir(session_id)
        json_path = session_dir / "session.json"
        svg_path = session_dir / "session.svg"

        if not json_path.exists() or not svg_path.exists():
            flash("Session expired or invalid", "danger")
            return redirect(url_for("translate.dashboard"))

        try:
            session_data = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            flash("Error loading translation session", "danger")
            return redirect(url_for("translate.dashboard"))

        filename = session_data.get("filename")
        lang = session_data.get("lang")
        mapping_dict = session_data.get("mapping", {})

        mapping = TranslationMapping.from_any(mapping_dict)

        # Update mapping with submitted translations, IGNORE empty translations
        for orig, trans in zip(originals, translations, strict=False):
            trans = trans.strip()
            if not trans:
                continue  # ignore empty inputs - do not delete on empty (MVP)

            # Update mapping.new
            mapping.new.setdefault(orig, {})[lang] = trans

        # Inject into a new temporary file inside the session folder
        output_file = session_dir / f"translated_{filename}"

        try:
            inject_result: InjectResult = inject_step_one_file(
                file=svg_path,
                translations=mapping,
                output_file=output_file,
                overwrite_translations=True,
            )
        except Exception:
            logger.exception("Failed during SVG translation injection")
            inject_result = InjectResult(
                result=False,
                msg="Failed during SVG translation injection",
                new_languages_count=None,
            )

        if not inject_result.result:
            flash(f"Translation injection failed: {inject_result.msg}", "danger")
            return redirect(url_for("translate.edit", session_id=session_id))

        # Handle Action: Download
        if action == "download":
            if not output_file.exists():
                flash("Translated file not found", "danger")
                return redirect(url_for("translate.edit", session_id=session_id))

            # Stream the modified SVG directly to the user
            response = send_file(
                output_file,
                mimetype="image/svg+xml",
                as_attachment=True,
                download_name=filename,
            )
            return response

        # Handle Action: Upload
        user_payload = load_auth_payload(g._current_user)
        site = get_user_site(user_payload)
        if not site:
            flash("OAuth session error. Please log in again.", "danger")
            return redirect(url_for("translate.dashboard"))

        upload_service = UploadService(site)
        summary = f"Added/Updated '{lang}' translations"
        upload_res = upload_service.upload_svg(
            filename=filename,
            file_path=output_file,
            summary=summary,
        )

        # Clean up session directory upon upload success/completion
        if session_dir.exists():
            shutil.rmtree(session_dir)

        if upload_res.ok:
            commons_link = f"https://commons.wikimedia.org/wiki/File:{filename}"
            flash(
                f"Successfully uploaded to <a href='{commons_link}' target='_blank' rel='noopener noreferrer'>Wikimedia Commons</a>!",
                "success",
            )
            return redirect(url_for("translate.dashboard"))
        elif upload_res.error == "skipped" or upload_res.msg == "File already exists with same content":
            flash("No translation changes detected or file already exists with identical content.", "warning")
            return redirect(url_for("translate.dashboard"))
        else:
            flash(
                f"Failed to upload file: {upload_res.error or 'unknown'} - {upload_res.error_details or ''}",
                "danger",
            )
            return redirect(url_for("translate.dashboard"))


class TranslateView:
    """Registrar class to bind translate MethodViews to a Blueprint."""

    @staticmethod
    def register(bp: Blueprint) -> None:
        """
        Register all translate URL rules on the provided blueprint.
        """
        # ------------------------------------------------------------------
        # Active MethodView Routes
        # ------------------------------------------------------------------
        bp.add_url_rule("/", view_func=TranslateDashboardView.as_view("dashboard"))
        bp.add_url_rule("/edit", view_func=TranslateEditView.as_view("edit"))
        bp.add_url_rule("/save", view_func=TranslateSaveView.as_view("save"))

__all__ = [
    "TranslateDashboardView",
    "TranslateEditView",
    "TranslateSaveView",
    "TranslateView",
]
