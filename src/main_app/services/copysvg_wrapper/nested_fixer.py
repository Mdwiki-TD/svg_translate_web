from __future__ import annotations

import logging
from pathlib import Path

from CopySVGTranslation import SVGTranslationService, TranslationConfig  # type: ignore
from CopySVGTranslation.nested.objects import RepairResult  # type: ignore

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
            sort_switches=True,
        )
        self.service = SVGTranslationService(config=config)

    def analyze_file(self, svg_path: Path | str) -> list[str]:
        result = self.service.analyze_nested(svg_path)
        if result.success and result.data is not None:
            return result.data
        return []

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
