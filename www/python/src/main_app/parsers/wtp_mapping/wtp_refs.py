"""
Citation parser for WikiText reference tags
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import cached_property

import wikitextparser as wtp

logger = logging.getLogger(__name__)


@dataclass
class WtpRef:
    """Represents a citation reference"""

    tag: wtp.Tag

    @property
    def attrs(self) -> dict[str, str]:
        return self.tag.attrs

    @property
    def tag_str(self) -> str:
        return self.tag.string

    @property
    def contents(self) -> str:
        return self.tag.contents or ""

    @property
    def match_key(self) -> tuple[str, str]:
        return (self.name, self.group)

    @property
    def name(self) -> str:
        """Get citation name"""
        return self.tag.attrs.get("name", "").strip()

    def is_self_closing(self) -> bool:
        return not self.tag.contents or not self.tag.contents.strip()

    @property
    def group(self) -> str:
        return (self.tag.get_attr("group") or "").strip()

    @property
    def span(self) -> tuple[int, int]:
        return self.tag.span

    def to_short(self) -> str:
        """Build a self-closing tag that keeps all original attributes."""
        if self.is_self_closing() and self.tag_str.rstrip().endswith("/>"):
            return self.tag_str

        clone = wtp.Tag(self.tag_str)
        clone.contents = ""
        return clone.string.replace("></ref>", " />")

    @classmethod
    def load(cls, ref: wtp.Tag) -> WtpRef:
        return cls(tag=ref)


@dataclass
class WtpRefs:
    """Parser for extracting reference tags and citations from WikiText."""

    parsed: wtp.WikiText

    @classmethod
    def load(
        cls,
        text: str = "",
        parsed: wtp.WikiText | None = None,
    ) -> WtpRefs:
        return cls(
            parsed=parsed or wtp.parse(text),
        )

    # ---------- helpers ----------

    @cached_property
    def all_refs(self) -> list[WtpRef]:
        """Extract all citation reference tags from text"""
        return [WtpRef.load(t) for t in self.parsed.get_tags("ref")]

    @property
    def full_refs(self) -> list[WtpRef]:
        return [x for x in self.all_refs if not x.is_self_closing()]

    @property
    def full_named_refs(self) -> list[WtpRef]:
        return [x for x in self.full_refs if x.name]

    @property
    def short_refs(self) -> list[WtpRef]:
        return [x for x in self.all_refs if x.is_self_closing()]

    @staticmethod
    def list_wtpref_to_dict(data: list[WtpRef]) -> dict[tuple[str, str], WtpRef]:
        # use match_key to match name and group, (self.name, self.group)
        return {x.match_key: x for x in data}


__all__ = [
    "WtpRef",
    "WtpRefs",
]
