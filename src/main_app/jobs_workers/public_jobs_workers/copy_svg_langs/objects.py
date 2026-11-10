"""
Objects for copy_svg_langs worker.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ...shared_objects import STATUS_LITERAL, StandardAdminSummary, WorkerMapping


@dataclass
class SvgLangsConfig:
    upload: bool | None
    upload_files: bool | None
    upload_limit: int = 0
    limit_items: int = 0
    overwrite_translations: bool = True
    overwrite_download: bool = True
    output_dir: Path | None = None
    output_dir_files: Path | None = None

    # --- Mapping ---
    merge_mapping_all_files: bool = False
    """ merge mapping for all files not only the main_file """

    @classmethod
    def load(
        cls,
        title: str,
        args: dict[str, Any],
        svg_data_path: Path | str,
    ) -> SvgLangsConfig:
        output_dir = cls._compute_output_dir(title, svg_data_path)
        output_dir_files = (output_dir / "files") if output_dir else None

        try:
            limit_items = int(args.get("limit_items")) or 0
        except Exception:
            limit_items = 0

        upload_limit = args.get("upload_limit") or 0
        upload_limit = upload_limit if isinstance(upload_limit, int) else 0

        overwrite_translations = bool(args.get("overwrite_translations"))

        overwrite_download = True

        # if args.get("overwrite_download") is not None: overwrite_download = bool(args.get("overwrite_download"))

        return SvgLangsConfig(
            upload=args.get("upload"),
            upload_files=args.get("upload_files"),
            upload_limit=upload_limit,
            limit_items=limit_items,
            overwrite_translations=overwrite_translations,
            overwrite_download=overwrite_download,
            output_dir=output_dir,
            output_dir_files=output_dir_files,
        )

    @staticmethod
    def _compute_output_dir(title: str, svg_data_path: Path | str) -> Path:
        if not title:
            return None

        name = Path(title).name
        slug = re.sub(r"[^A-Za-z0-9._\- ]+", "_", str(name)).strip("._") or "untitled"
        slug = slug.replace(" ", "_").lower()
        out = Path(svg_data_path) / slug
        out.mkdir(parents=True, exist_ok=True)

        out_translated = out / "translated"
        out_translated.mkdir(parents=True, exist_ok=True)

        out_dir_main = out / "files"
        out_dir_main.mkdir(parents=True, exist_ok=True)

        return out


@dataclass
class StageDetail:
    name: str = ""
    status: STATUS_LITERAL = "pending"
    message: str = ""
    data: Any = None

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Stages:
    text: StageDetail = field(
        default_factory=lambda: StageDetail(
            name="text",
            message="Getting text",
        )
    )
    titles: StageDetail = field(
        default_factory=lambda: StageDetail(
            name="titles",
            message="Getting titles",
        )
    )
    translations: StageDetail = field(
        default_factory=lambda: StageDetail(
            name="translations",
            message="Getting translations",
        )
    )
    processfiles: StageDetail = field(
        default_factory=lambda: StageDetail(
            name="processfiles",
            message="process Files",
        )
    )

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StepResult:
    result: bool | None = None
    msg: str = ""
    details: dict[str, Any] | None = None

    def _update(self, result: bool | None = None, msg: str = "", details: dict[str, Any] | None = None) -> None:
        self.result = result

        if msg:
            self.msg = msg

        if details:
            self.details = details


@dataclass
class FileSteps:
    download: StepResult = field(default_factory=lambda: StepResult())
    nested: StepResult = field(default_factory=lambda: StepResult())
    translations: StepResult = field(
        default_factory=lambda: StepResult(msg="", details={"new": 0, "updated": 0, "inserted": 0, "new_list": []})
    )
    inject: StepResult = field(default_factory=lambda: StepResult())
    upload: StepResult = field(default_factory=lambda: StepResult())


@dataclass
class FilesProcessedItem:
    title: str
    file_path: str | None = None
    status: STATUS_LITERAL = "pending"
    error: str | None = None
    steps: FileSteps = field(default_factory=lambda: FileSteps())
    is_mapping_merged: bool = False

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CopySvgLangsWorkerObject(WorkerMapping):
    summary: StandardAdminSummary = field(default_factory=StandardAdminSummary)
    title: str | None = None
    main_title: str | None = None

    stages: Stages = field(default_factory=Stages)
    translations: list[dict[str, str]] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)

    files_processed: list[FilesProcessedItem] = field(default_factory=list)
    files_success: list[FilesProcessedItem] = field(default_factory=list)
    files_skipped: list[FilesProcessedItem] = field(default_factory=list)
    files_failed: list[FilesProcessedItem] = field(default_factory=list)

    mapping_mereged: int = 0
    note: str = ""

    def to_json(self) -> dict[str, Any]:
        """
        Converts the dataclass instance back to its original dictionary format.
        """
        return asdict(self)


__all__ = [
    "SvgLangsConfig",
    "StepResult",
    "FileSteps",
    "FilesProcessedItem",
    "CopySvgLangsWorkerObject",
]
