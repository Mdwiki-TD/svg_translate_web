from __future__ import annotations

import json
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from ...api_services.files_service import FilesService
from ...services.copysvg_wrapper import (
    ExtractResult,
    InjectResult,
    extract_from_path,
    inject_step_one_file,
)
from .mapping import DiffResult

logger = logging.getLogger(__name__)


def _extract_from_path(file_path: Path) -> dict[str, Any] | None:
    """Extract translations from a local file path.

    Args:
        file_path: Path to the SVG file.

    Returns:
        Translations dict or None on failure.
    """
    step_result: ExtractResult = extract_from_path(file_path)

    if not step_result.success:
        flash(f"Invalid or empty translation data in {file_path.name}.", "danger")
        flash(f"Error code: {step_result.error}", "danger")
        return None

    file_translations = step_result.translations or {}
    if not isinstance(file_translations, dict):
        flash(f"Invalid or empty translation data in {file_path.name}", "danger")
        return None

    if file_translations and not any(file_translations.values()):
        flash(f"Empty translation data in {file_path.name}", "danger")
        return None

    return file_translations


class InjectRoutes:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self.files_service = FilesService()
        self._setup_routes()

    def _setup_routes(self) -> None:
        routes = [
            ("/", "GET", self.dashboard),
            ("/", "POST", self.inject_post),
            ("/<string:source>/<string:target>", "GET", self.inject_get),
            ("/demo", "GET", self.inject_demo),
        ]
        for rule, method, target in routes:
            self.bp.route(rule, methods=[method])(target)

    def dashboard(self) -> str:
        """Display the inject form."""
        return render_template(
            "inject/form.html",
        )

    def inject_post(self) -> str:
        """Validate form inputs and redirect to the GET endpoint."""
        source = request.form.get("source_filename", "").strip()
        target = request.form.get("target_filename", "").strip()

        if not source or not target:
            flash("Please provide both source and target file names", "danger")
            return render_template(
                "inject/form.html",
                source_filename=source,
                target_filename=target,
            )
        _source = source.replace(" ", "_")
        _target = target.replace(" ", "_")
        return redirect(url_for("inject.inject_get", source=_source, target=_target))

    def inject_get(self, source: str, target: str) -> str:
        """Execute the inject workflow and render the result."""

        source, source_display = self._format_source_path(source)
        target, target_display = self._format_source_path(target)

        # Validate filenames
        if not source or not target:
            flash("Please provide both source and target file names", "danger")
            return render_template("inject/form.html")

        for name, label in [(source, "Source"), (target, "Target")]:
            if name != Path(name).name or name in {".", ".."}:
                flash(f"Invalid {label.lower()} file name: {name}", "danger")
                return render_template("inject/form.html")

        # Check files exist on Commons
        source_info = self.files_service.get_file_info(f"File:{source}")
        if not source_info.exists:
            flash(f"Source file File:{source} does not exist", "danger")
            logger.error("Source file info: %s", source_info.to_json())
            return render_template(
                "inject/form.html",
                source_filename=source_display,
                target_filename=target_display,
            )

        target_info = self.files_service.get_file_info(f"File:{target}")
        if not target_info.exists:
            flash(f"Target file File:{target} does not exist", "danger")
            logger.error("Target file info: %s", target_info.to_json())
            return render_template(
                "inject/form.html",
                source_filename=source_display,
                target_filename=target_display,
            )

        temp_dir = Path(tempfile.mkdtemp())
        try:
            # Step 1: Download and extract from source
            source_translations = self._download_and_extract(source, temp_dir)
            if source_translations is None:
                return render_template(
                    "inject/form.html",
                    source_filename=source_display,
                    target_filename=target_display,
                )

            # Step 2: Download and extract from target (before inject)
            target_before = self._download_and_extract(target, temp_dir)
            if target_before is None:
                return render_template(
                    "inject/form.html",
                    source_filename=source_display,
                    target_filename=target_display,
                )

            data = self.load_data(source, target, temp_dir, source_translations, target_before)

            return render_template(
                "inject/result.html",
                source_filename=source_display,
                target_filename=target_display,
                data=data,
            )

        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def _format_source_path(self, source: str) -> tuple[str, str]:
        source = source.strip()
        source_display = source

        # Strip "File:" prefix for processing, keep for display
        if source.lower().startswith("file:"):
            source = source[5:].lstrip()
            source_display = f"File:{source}"
        else:
            source_display = f"File:{source}"

        return source, source_display

    def load_data(self, source, target, temp_dir, source_translations, target_before):
        data = {}
        # Extract unique languages from source_translations['new']
        src_langs_sorted = self.extract_sorted_languages(source_translations.get("new") or {})

        # Step 3: Copy target file to output location and inject
        target_file_path = temp_dir / target
        output_dir = temp_dir / "output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / target

        inject_result: InjectResult = inject_step_one_file(
            file_path=target_file_path,
            translations=source_translations,
            output_file=output_file,
            overwrite_translations=True,
        )

        # Step 4: Re-extract from the injected file (only if inject succeeded)
        target_after: dict[str, Any] | None = None
        diff = DiffResult()

        target_changed = inject_result.result is True

        if target_changed and output_file.exists():
            target_after = _extract_from_path(output_file)
            if target_after is not None and target_before is not None:
                diff = DiffResult.compute_diff(target_before, target_after)

        diff.target_changed = target_changed

        data = {
            "source_translations": source_translations,
            "src_langs_sorted": src_langs_sorted,
            "target_before": target_before,
            "inject_result": inject_result.to_json(),
            "target_after": target_after,
            "diff": diff.to_json(),
        }

        return data

    def extract_sorted_languages(self, new_translations) -> list[str]:
        src_langs_sorted = []
        src_langs = set()

        for entry in new_translations.values():
            if isinstance(entry, dict):
                src_langs.update(entry.keys())

        src_langs_sorted = sorted(src_langs)
        return src_langs_sorted

    def inject_demo(self) -> str:
        dir = Path(__file__).parent.parent.parent.parent
        file_path = Path(f"{dir}/templates/inject/example.json")
        file_data = {}
        if file_path.exists():
            try:
                file_data = json.loads(file_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                logger.exception(f"Failed to read demo data from {file_path}")
        else:
            logger.error(f"File {file_path} not found")

        return render_template(
            "inject/result.html",
            source_filename="File:parkinsons-disease-prevalence-ihme,World,1990.svg",
            target_filename="File:Parkinsons-disease-prevalence-ihme,_1990_to_2021,_BMU.svg",
            data=file_data,
        )

    def _download_and_extract(self, filename: str, temp_dir: Path) -> dict[str, Any] | None:
        """Download a file from Commons and extract translations.

        Args:
            filename: The file name (without "File:" prefix).
            temp_dir: Directory to download into.

        Returns:
            Translations dict or None on failure (with flash message).
        """
        result = self.files_service.download_and_save(title=filename, out_dir=temp_dir, overwrite_download=True)

        if result.result != "success" or not result.path:
            flash(f"Failed to download file: {filename}", "danger")
            return None

        file_path = Path(result.path)

        return _extract_from_path(file_path)


__all__ = [
    "InjectRoutes",
]
