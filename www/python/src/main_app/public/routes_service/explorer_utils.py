import json
import logging
from pathlib import Path
from typing import Any

from ...config import get_settings
from ...database.services import TemplateService

logger = logging.getLogger(__name__)


class ExplorerDataService:
    """Service for reading SVG data files from disk."""

    def __init__(
        self,
        svg_data_path: Path | None = None,
        template_service: TemplateService | None = None,
    ) -> None:
        """Initialize with optional dependencies.

        Args:
            svg_data_path: Path to SVG data directory. Falls back to config if None.
            template_service: Template service instance. Falls back to default if None.
        """
        self._svg_data_path = svg_data_path
        self._template_service = template_service

    def _get_svg_data_path(self) -> Path:
        """Get the SVG data path (lazy initialization)."""
        if self._svg_data_path is None:
            app_settings = get_settings()
            self._svg_data_path = Path(app_settings.paths.svg_data)
        return self._svg_data_path

    def _get_template_service(self) -> TemplateService:
        """Get the template service (lazy initialization)."""
        if self._template_service is None:
            self._template_service = TemplateService()
        return self._template_service

    def _validate_path_under_base(self, title: str, sub_dir: str) -> Path:
        """Resolve and validate that title/sub_dir is confined under BASE_SVG."""
        return _validate_path_under_base(title, sub_dir)

    def get_main_data(self, title, filename: str = "files_stats.json") -> dict[str, Any]:
        """Load JSON data file."""
        return get_main_data(title, filename)

    def get_files_full_path(self, title, sub_dir) -> tuple:
        """List all files in subdirectory."""
        return get_files_full_path(title, sub_dir)

    def get_files(self, title, sub_dir) -> tuple:
        """List SVG files in subdirectory."""
        return get_files(title, sub_dir)

    def get_languages(self, title: str, translations_data: dict | None = None) -> list:
        """Extract language codes from translations."""
        return get_languages(title, translations_data)

    def get_informations(self, title: str) -> dict[str, Any]:
        """Aggregate file/template/language info."""
        return get_informations(title)


def load_svg_data_path() -> Path:
    # return Path("I:/TOOLFORGE_TOOLS/copy-svg-langs.toolforge.org/data/svg_data")
    # return Path(__name__).parent.parent.parent / "svg_data"
    app_settings = get_settings()
    return Path(app_settings.paths.svg_data)


def _validate_path_under_base(title: str, sub_dir: str) -> Path:
    """Resolve and validate that title/sub_dir is confined under BASE_SVG."""
    svg_data_path = load_svg_data_path()
    try:
        candidate = (svg_data_path / title / sub_dir).resolve()
    except (ValueError, OSError):
        raise PermissionError(f"Invalid path: title={title!r}, sub_dir={sub_dir!r}") from None

    if svg_data_path not in candidate.parents and candidate != svg_data_path:
        raise PermissionError(f"Path traversal attempt blocked: {candidate}")

    return candidate


def get_main_data(title, filename: str = "files_stats.json") -> dict[str, Any]:
    svg_data_path = load_svg_data_path()
    file_path = svg_data_path / title / (filename or "files_stats.json")
    if not file_path.exists():
        return {}
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        return data
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        logger.exception(f"Failed to read or parse {file_path}")
        return {}


def get_files_full_path(title, sub_dir) -> tuple:
    # title_path = svg_data_path / title / sub_dir
    svg_data_path = load_svg_data_path()

    try:
        title_path = _validate_path_under_base(title, sub_dir)
    except PermissionError as e:
        logger.exception(str(e))
        return [], svg_data_path / title / sub_dir

    if not title_path.exists():
        logger.error(f"Title path {title_path} does not exist")
        return [], title_path

    files = [str(x.name) for x in title_path.glob("*")]

    return files, title_path


def get_files(title, sub_dir) -> tuple:
    # title_path = svg_data_path / title / sub_dir
    svg_data_path = load_svg_data_path()
    try:
        title_path = _validate_path_under_base(title, sub_dir)
    except PermissionError as e:
        logger.exception(str(e))
        return [], svg_data_path / title / sub_dir

    if not title_path.exists():
        logger.error(f"Title path {title_path} does not exist")
        return [], title_path

    files = [x.name for x in title_path.glob("*.svg")]

    return files, title_path


def get_languages(title: str, translations_data: dict | None = None) -> list:
    # ---
    languages: list[Any] = []
    # ---
    if not translations_data:
        translations_data = get_main_data(title, "translations.json") or {}
    # ---
    if not translations_data:
        return []
    # ---
    new = translations_data.get("new", {})
    # ---
    for key, v in new.items():
        if key == "default_tspans_by_id":
            continue
        if isinstance(v, dict):
            languages.extend(v.keys())
    # ---
    return sorted(set(languages))


def get_informations(title: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    downloaded, title_path = get_files(title, "files")
    translated, _ = get_files(title, "translated")

    full_title = f"Template:OWID/{title}" if not title.startswith("Template:OWID/") else title
    full_title = full_title.replace("_", " ")
    template = TemplateService().get_template_by_title(full_title)
    if not template:
        logger.info(f"Template {full_title} not found")

    data = get_main_data(title)
    len_titles = len(data.get("titles", []))

    main_file = template.main_file if template else ""

    if main_file and not main_file.lower().startswith("file:"):
        main_file = f"File:{main_file}"

    languages = get_languages(title, data.get("translations"))

    # Instantiating set(translated) outside the list comprehension reduces lookup complexity to O(N + M)
    translated_set = set(translated)
    not_translated = [x for x in downloaded if x not in translated_set]
    downloaded_set = {f.lower() for f in downloaded}
    not_downloaded = [
        (f"File:{x}" if not x.lower().startswith("file:") else x)
        for x in data.get("titles", [])
        if x.lower() not in downloaded_set
    ]

    result = {
        "title": title,
        "title_dir": title,
        "main_file": main_file,
        "len_titles": len_titles,
        "languages": ", ".join(languages),
        "path": str(title_path.parent),
        "len_files": {
            "not_downloaded": len(not_downloaded),
            "downloaded": len(downloaded),
            "translated": len(translated),
            "not_translated": len(not_translated),
        },
        "not_downloaded": not_downloaded,
    }
    return result


__all__ = [
    "get_files_full_path",
    "get_files",
    "get_languages",
    "get_informations",
]
