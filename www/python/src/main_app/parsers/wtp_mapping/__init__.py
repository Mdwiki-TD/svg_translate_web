"""Parsers for WikiText elements"""

from __future__ import annotations

from .wtp_refs import WtpRef, WtpRefs
from .wtp_refs_temps import WtpRefsTemps
from .wtp_temps import WtpTemplates

__all__ = [
    "WtpRefsTemps",
    "WtpRef",
    "WtpTemplates",
    "WtpRefs",
]
