"""
Worker module for copy_svg_langs.
"""

from __future__ import annotations

import logging
from typing import Any

from .forms import CopySvgLangsForm

logger = logging.getLogger(__name__)


def setup_svg_langs_form(all_settings: dict[str, Any] | None = None) -> CopySvgLangsForm:
    form = CopySvgLangsForm()
    # set upload default dynamically only on GET (first load)
    upload_disabled_by_default = bool(
        all_settings and all_settings.get("copy_svg_langs_upload_disabled_by_default", False)
    )
    form.upload.data = not upload_disabled_by_default
    return form

__all__ = [
    "setup_svg_langs_form",
]
