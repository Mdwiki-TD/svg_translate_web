"""
Step for extracting wikitext for a Commons file.
Step for extracting SVG titles from wikitext.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from mwclient.client import Site

from ....api_services import MwClientPage
from ....utils.new_wikitext import SvgFilesCollector

logger = logging.getLogger(__name__)


@dataclass
class ExtractTitles:
    success: bool
    titles: list[str]
    main_title: str | None
    error: str | None
    message: str | None

    @classmethod
    def load(cls, data: dict[str, Any]) -> ExtractTitles:
        return cls(
            success=data.get("success", False),
            titles=data.get("titles") or [],
            main_title=data.get("main_title"),
            error=data.get("error"),
            message=data.get("message"),
        )


class ExtractSteps:
    @staticmethod
    def extract_text_step(title: str, site: Site | None = None) -> dict[str, Any]:
        """Fetch wikitext for a Commons file.

        Args:
            title: Commons title whose wikitext should be retrieved.

        Returns:
            dict with keys: success (bool), text (str), error (str|None)
        """
        logger.info(f"Extracting wikitext for: {title}")
        if not title:
            logger.error("No title found")
            return {"success": False, "text": "", "error": "No title found"}

        try:
            text = MwClientPage(title, site).get_text()  # pyright: ignore[reportArgumentType]
        except Exception:
            logger.exception(f"Failed to fetch wikitext for title: {title}")
            return {"success": False, "text": "", "error": "Failed to fetch wikitext"}

        if not text:
            logger.error(f"No wikitext found for title: {title}")
            return {"success": False, "text": "", "error": "No wikitext found"}

        return {"success": True, "text": text, "error": None}

    @staticmethod
    def extract_titles(
        text: str,
        manual_main_title: str | None = None,
    ) -> ExtractTitles:
        """Extract SVG titles from wikitext.

        Args:
            text: Wikitext retrieved from the main Commons page.
            manual_main_title: Optional title to use instead of the extracted main_title.

        Returns:
            dict with keys: success (bool), main_title (str|None), titles (list[str]), error (str|None)
        """
        data = SvgFilesCollector().get_files_list_data(text)

        main_title = data["main_title"]
        titles = data["titles"]

        if manual_main_title:
            main_title = manual_main_title

        if not titles or not main_title:
            error = f"No titles or main title found. Manual main title was: '{manual_main_title}'"
            logger.error(error)
            return ExtractTitles(
                success=False,
                main_title=main_title,
                titles=titles or [],
                error=error,
                message="",
            )

        message = f"Found {len(titles)} titles"
        return ExtractTitles(
            success=True,
            main_title=main_title,
            titles=titles,
            error=None,
            message=message,
        )


__all__ = [
    "ExtractSteps",
]
