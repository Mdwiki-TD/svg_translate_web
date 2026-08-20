from __future__ import annotations

import logging
from pathlib import Path

from CopySVGTranslation import SVGTranslationService, TranslationConfig  # type: ignore
from CopySVGTranslation.nested.objects import RepairResult  # type: ignore
from lxml import etree

SVG_NS = "http://www.w3.org/2000/svg"
SVG_TSPAN = f"{{{SVG_NS}}}tspan"
SVG_A = f"{{{SVG_NS}}}a"

logger = logging.getLogger(__name__)


class NestedStructureService:
    """Wrapper around SVGTranslationService for analyzing and repairing nested SVG structures."""

    def __init__(
        self,
        strategy: str = "flatten",
        also_fix_a: bool = True,
    ) -> None:
        self.strategy = strategy
        self.also_fix_a = also_fix_a
        config = TranslationConfig(
            nested_strategy=strategy,
        )
        self.service = SVGTranslationService(config=config)

    def analyze_file(self, svg_path: Path | str) -> list[str]:
        """Return nested structures that the configured flatten strategy can repair.

        The upstream detector reports every ``<a>`` or ``<tspan>`` with element
        children.  A valid title link, for example, normally has the structure
        ``<a><text><tspan>…</tspan></text></a>``.  The flattener intentionally
        does not alter that link, so treating it as a nested-tag error causes a
        false failure.  Only nested ``<tspan>`` or ``<a>`` descendants of a
        ``<tspan>`` are repairable by the flatten strategy.
        """
        result = self.service.analyze_nested(svg_path)
        if not result.success or result.data is None:
            return []

        try:
            parser = etree.XMLParser(resolve_entities=False, no_network=True)
            root = etree.parse(str(svg_path), parser).getroot()
        except (etree.XMLSyntaxError, OSError) as exc:
            logger.error("Failed to parse SVG file %s while filtering nested structures: %s", svg_path, exc)
            return []

        repairable = []
        for tspan in root.findall(f".//{SVG_TSPAN}"):
            nested_tspans = tspan.findall(f".//{SVG_TSPAN}")
            nested_links = tspan.findall(f".//{SVG_A}")
            if nested_tspans or nested_links:
                repairable.append(etree.tostring(tspan, pretty_print=False).decode("utf-8"))

        return repairable

    def repair_file(
        self,
        svg_path: Path | str,
        output: Path | str | None = None,
        strategy: str | None = None,
    ) -> RepairResult:
        strat = strategy or self.strategy
        out_path = output or svg_path
        result = self.service.repair_nested(
            svg_path,
            output=out_path,
            strategy=strat,
            save=True,
        )
        if result.success and isinstance(result.data, RepairResult):
            return result.data
        elif isinstance(result.data, RepairResult):
            return result.data
        else:
            return RepairResult(
                success=False,
                len_tags_before_fix=0,
                len_tags_after_fix=0,
                len_tags_fixed=0,
                warnings=[result.error] if result.error else [],
            )


__all__ = [
    "NestedStructureService",
]
