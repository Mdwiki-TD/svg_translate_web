"""Parsers for WikiText elements"""

from __future__ import annotations

from .wtp_mapping import WtpRef, WtpRefs, WtpRefsTemps, WtpTemplates
from .template_editor import TemplateEditor

__all__ = [
    "TemplateEditor",
    "WtpRefsTemps",
    "WtpRef",
    "WtpTemplates",
    "WtpRefs",
]
