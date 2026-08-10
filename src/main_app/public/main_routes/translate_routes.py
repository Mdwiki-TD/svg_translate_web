from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from ...api_services import FilesService, UploadService, get_user_site
from ...shared.copysvg_wrapper import extract_from_path, inject_step_one_file
from ..auth.utils import oauth_required
from ..utils.routes_utils import load_auth_payload

logger = logging.getLogger(__name__)


class TranslateRoutes:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self.files_service = FilesService()
        self._setup_routes()

    def _setup_routes(self) -> None:
        self.bp.route("/", methods=["GET"])(oauth_required(self.dashboard))
        self.bp.route("/select", methods=["POST"])(oauth_required(self.select_post))
        self.bp.route("/edit", methods=["GET"])(oauth_required(self.edit_get))
        self.bp.route("/save", methods=["POST"])(oauth_required(self.save_post))

    def dashboard(self) -> str:
        """Display select form with filename and language fields."""
        return render_template("translate/form.html")

    def select_post(self) -> Any:
        """Process selection form and redirect to edit view with query parameters."""
        filename = request.form.get("filename", "").strip()
        lang = request.form.get("lang", "").strip()

        if not filename or not lang:
            flash("Please provide both file name and language code", "danger")
            return redirect(url_for("translate.dashboard"))

        return redirect(url_for("translate.edit_get", filename=filename, lang=lang))

    def edit_get(self) -> Any:
        """Display English text segments with parallel translation inputs for editing."""
        filename = request.args.get("filename", "").strip()
        lang = request.args.get("lang", "").strip()

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

        temp_dir = Path(tempfile.mkdtemp())
        try:
            download_result = self.files_service.download_and_save(
                title=processed_filename,
                out_dir=temp_dir,
                overwrite_download=True,
            )
            if download_result.result != "success" or not download_result.path:
                flash(f"Failed to download file: {processed_filename}", "danger")
                return redirect(url_for("translate.dashboard"))

            file_path = Path(download_result.path)
            extract_result = extract_from_path(file_path, fast_return_false=False)
            mapping = extract_result.mapping

            if extract_result is None or mapping is None or extract_result.error:
                flash(f"Failed to parse or extract translations from {processed_filename}", "danger")
                return redirect(url_for("translate.dashboard"))

            all_keys = sorted(list(set(mapping.new.keys()) | set(mapping.title_new.keys())))

            texts_with_translations = []
            for key in all_keys:
                existing_trans = ""
                if key in mapping.new and lang in mapping.new[key]:
                    existing_trans = mapping.new[key][lang]
                elif key in mapping.title_new and lang in mapping.title_new[key]:
                    existing_trans = mapping.title_new[key][lang]

                texts_with_translations.append({
                    "original": key,
                    "translation": existing_trans,
                })

            return render_template(
                "translate/edit.html",
                filename=prefixed_file_name,
                lang=lang,
                texts_with_translations=texts_with_translations,
            )
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def save_post(self) -> Any:
        """Inject translations and upload to Commons."""
        filename = request.form.get("filename", "").strip()
        lang = request.form.get("lang", "").strip()
        originals = request.form.getlist("originals")
        translations = request.form.getlist("translations")

        if not filename or not lang:
            flash("Missing file name or language code", "danger")
            return redirect(url_for("translate.dashboard"))

        processed_filename = filename
        if processed_filename.lower().startswith("file:"):
            processed_filename = processed_filename[5:].lstrip()

        prefixed_file_name = f"File:{processed_filename}"

        temp_dir = Path(tempfile.mkdtemp())
        try:
            download_result = self.files_service.download_and_save(
                title=processed_filename,
                out_dir=temp_dir,
                overwrite_download=True,
            )
            if download_result.result != "success" or not download_result.path:
                flash(f"Failed to download file: {processed_filename}", "danger")
                return redirect(url_for("translate.dashboard"))

            file_path = Path(download_result.path)
            extract_result = extract_from_path(file_path, fast_return_false=False)
            mapping = extract_result.mapping

            if extract_result is None or mapping is None or extract_result.error:
                flash(f"Failed to parse or extract translations from {processed_filename}", "danger")
                return redirect(url_for("translate.dashboard"))

            # Update mapping with submitted translations
            for orig, trans in zip(originals, translations):
                trans = trans.strip()
                if not trans:
                    if orig in mapping.new:
                        mapping.new[orig].pop(lang, None)
                    if orig in mapping.title_new:
                        mapping.title_new[orig].pop(lang, None)
                else:
                    if orig in mapping.new:
                        mapping.new[orig][lang] = trans
                    if orig in mapping.title_new:
                        mapping.title_new[orig][lang] = trans
                    if orig not in mapping.new and orig not in mapping.title_new:
                        mapping.new.setdefault(orig, {})[lang] = trans

            output_dir = temp_dir / "output"
            output_dir.mkdir(exist_ok=True)
            output_file = output_dir / processed_filename

            # Inject
            inject_result = inject_step_one_file(
                file_path=file_path,
                translations=mapping,
                output_file=output_file,
                overwrite_translations=True,
            )

            if not inject_result.result:
                flash(f"Translation injection failed: {inject_result.msg}", "danger")
                return redirect(url_for("translate.edit_get", filename=filename, lang=lang))

            # Build OAuth site
            user_payload = load_auth_payload(g._current_user)
            site = get_user_site(user_payload)
            if not site:
                flash("OAuth session error. Please log in again.", "danger")
                return redirect(url_for("translate.dashboard"))

            # Upload to Commons
            upload_service = UploadService(site)
            summary = f"Added/Updated '{lang}' translations using Copy SVG Translations tool"
            upload_res = upload_service.upload_svg(
                filename=processed_filename,
                file_path=output_file,
                summary=summary,
            )

            if upload_res.ok:
                flash(f"Successfully updated translations and uploaded {prefixed_file_name} to Wikimedia Commons!", "success")
                return redirect(url_for("translate.dashboard"))
            elif upload_res.error == "skipped" or upload_res.msg == "File already exists with same content":
                flash(f"Skipped: No translation changes detected in {prefixed_file_name}.", "warning")
                return redirect(url_for("translate.edit_get", filename=filename, lang=lang))
            else:
                flash(f"Failed to upload file: {upload_res.error or 'unknown'} - {upload_res.error_details or ''}", "danger")
                return redirect(url_for("translate.edit_get", filename=filename, lang=lang))

        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)


__all__ = [
    "TranslateRoutes",
]
