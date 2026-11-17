"""
Citation parser for WikiText reference tags
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import cached_property

from .wtp_refs import WtpRef, WtpRefs
from .wtp_temps import WtpTemplates

logger = logging.getLogger(__name__)


@dataclass
class WtpRefsTemps:
    """Parser for extracting reference tags and citations from WikiText."""

    tpls: WtpTemplates
    refs: WtpRefs

    @classmethod
    def load(cls, text: str) -> WtpRefsTemps:
        return cls(
            tpls=WtpTemplates.load(text),
            refs=WtpRefs.load(text),
        )

    # ---------- Templates related ----------

    @cached_property
    def tpl_refs(self) -> list[WtpRef]:
        return [r for r in self.refs.all_refs if self.tpls.contains(r.span)]

    @cached_property
    def body_refs(self) -> list[WtpRef]:
        return [r for r in self.refs.all_refs if not self.tpls.contains(r.span)]

    @cached_property
    def tpl_full_refs(self) -> dict[str, str]:
        """Full refs found inside templates only."""
        return self._full_refs_of(self.tpl_refs)

    @cached_property
    def body_full_refs(self) -> dict[str, str]:
        """Full refs found in the body only."""
        return self._full_refs_of(self.body_refs)

    @staticmethod
    def _full_refs_of(refs: list[WtpRef]) -> dict[str, str]:
        out: dict[str, str] = {}
        for r in refs:
            content = r.contents.strip()
            if r.name and content:
                full_str = r.tag_str
                out.setdefault(r.name, full_str)
        return out

    @cached_property
    def body_short_names(self) -> set[str]:
        return {r.name for r in self.body_refs if r.name and r.is_self_closing()}


__all__ = [
    "WtpRefsTemps",
]
