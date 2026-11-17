""" """

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import cached_property

import wikitextparser as wtp

logger = logging.getLogger(__name__)


def _inside(span, outer):
    return outer[0] <= span[0] and span[1] <= outer[1]


@dataclass
class WtpTemplates:
    text: str
    parsed: wtp.WikiText

    @classmethod
    def load(
        cls,
        text: str = "",
        parsed: wtp.WikiText | None = None,
    ) -> WtpTemplates:
        return cls(
            text=text,
            parsed=parsed or wtp.parse(text),
        )

    @cached_property
    def all_spans(self) -> list[tuple[int, int]]:
        return [t.span for t in self.parsed.templates]

    @cached_property
    def ref_spans(self) -> list[tuple[int, int]]:
        return [r.span for r in self.parsed.get_tags("ref")]

    @cached_property
    def top_tpls(self) -> list[tuple[int, int]]:
        """Top-level templates: not inside another template or a ref tag."""
        spans = [
            s
            for s in self.all_spans
            if not any(o != s and _inside(s, o) for o in self.all_spans)
            and not any(_inside(s, rs) for rs in self.ref_spans)
        ]
        logger.debug("Found %d top-level templates", len(spans))
        return spans

    def contains(self, span) -> bool:
        """Return True if the span is inside a top-level template."""
        return any(_inside(span, t) for t in self.top_tpls)


__all__ = [
    "WtpTemplates",
]
