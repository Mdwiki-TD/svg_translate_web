from __future__ import annotations

from .forms import setup_svg_langs_form
from .worker import CopySvgLangsWorker

__all__ = [
    "CopySvgLangsWorker",
    "setup_svg_langs_form",
]
