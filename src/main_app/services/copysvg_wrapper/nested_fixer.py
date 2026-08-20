from __future__ import annotations

import logging
from pathlib import Path

from CopySVGTranslation import NestedTspanDetector, NestedTspanFlattener  # type: ignore
from lxml import etree

from ..fix_nested.objects import DetectionResult, NestedStrategy, RepairResult

logger = logging.getLogger(__name__)


class MatchFixNestedTags:
    """
    Deprecated legacy wrapper. Use NestedStructureService instead.
    """

    def __init__(
        self,
        strategy: NestedStrategy = "flatten",
        also_fix_a: bool = True,
    ) -> None:
        self.strategy = strategy
        self.also_fix_a = also_fix_a
        self.detector = NestedTspanDetector()
        self.flattener = NestedTspanFlattener(strategy=strategy, also_fix_a=also_fix_a)

    def _get_root(
        self,
        path: Path | str,
        remove_blank_text: bool = False,
    ):
        parser = etree.XMLParser(
            remove_blank_text=remove_blank_text,
            resolve_entities=False,
            no_network=True,
        )
        try:
            tree = etree.parse(str(path), parser)
            return tree.getroot()
        except (etree.XMLSyntaxError, OSError) as exc:
            logger.error(f"Failed to parse SVG file {path}: {exc}")
            return None

    def match_nested(self, source_file: Path | str) -> list[str]:
        root = self._get_root(source_file)
        if root is None:
            return []

        return self.detector.find_in_tree_return_list(root)

    def detect_nested_tags(
        self,
        source_file: Path | str,
    ) -> DetectionResult:
        """Detect nested tags in SVG file."""
        nested = self.match_nested(source_file)
        return DetectionResult(
            count=len(nested),
            tags=nested,
        )

    def repair_file(
        self,
        source: Path | str,
        output: Path | str | None = None,
        strategy: NestedStrategy | None = None,
    ) -> RepairResult:
        """
        Repair nested tags in a file and write the result to another file.
        """
        src_path = Path(source)
        out_path = Path(output) if output else src_path
        warnings: list[str] = []

        if not src_path.exists():
            return RepairResult(
                success=False,
                len_tags_before_fix=0,
                len_tags_after_fix=0,
                warnings=[f"Source file does not exist: {src_path}"],
            )

        try:
            # Parse source file
            root = self._get_root(src_path)

            if root is None:
                return RepairResult(
                    success=False,
                    len_tags_before_fix=0,
                    len_tags_after_fix=0,
                    warnings=["Empty SVG root"],
                )

            # Count before fix
            len_before = len(self.detector.find_in_tree(root))

            # Apply repair
            chosen_strategy = strategy or self.strategy

            flattener = self.flattener
            if chosen_strategy != self.strategy:
                flattener = NestedTspanFlattener(strategy=chosen_strategy, also_fix_a=self.also_fix_a)

            root = flattener.process(root)

            # Count after fix
            len_after = len(self.detector.find_in_tree(root))

            # Write out
            self._save_file(root, out_path)

            return RepairResult(
                success=True,
                len_tags_before_fix=len_before,
                len_tags_after_fix=len_after,
                warnings=warnings,
            )

        except Exception as exc:
            logger.error("Failed to repair file %s: %s", src_path, exc)
            return RepairResult(
                success=False,
                len_tags_before_fix=0,
                len_tags_after_fix=0,
                warnings=[str(exc)],
            )

    def _save_file(
        self,
        root: etree._Element,
        out_path: Path | str,
    ) -> None:
        _str = etree.tostring(
            root,
            encoding="unicode",
            pretty_print=None,
        )  # pyright: ignore[reportCallIssue]

        if not out_path:
            raise Exception("new_path is None")

        out_path = Path(out_path)
        out_path.write_text(_str, encoding="utf-8")


__all__ = [
    "MatchFixNestedTags",
]
