"""Parsers for WikiText elements"""

from __future__ import annotations

from .template_editor import TemplateEditor
from .wtp_mapping import WtpRef, WtpRefs, WtpRefsTemps, WtpTemplates

__all__ = [
    "TemplateEditor",
    "WtpRefsTemps",
    "WtpRef",
    "WtpTemplates",
    "WtpRefs",
]
