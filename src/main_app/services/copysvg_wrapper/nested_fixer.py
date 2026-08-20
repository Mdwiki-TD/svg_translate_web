from __future__ import annotations

import logging
from pathlib import Path

from CopySVGTranslation import NestedTspanDetector, NestedTspanFlattener  # type: ignore
from lxml import etree

from ..fix_nested.objects import NestedStrategy, RepairResult

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

    def analyze_file(
        self,
        source: Path | str,
    ) -> list[str]:
        """
        Detect nested tspan/a structures. Read-only.
        Returns a list of XML strings representing the nested elements found.
        """
        path = Path(source)
        if not path.exists():
            logger.error("File does not exist: %s", path)
            return []

        tree = self._get_tree(path, remove_blank_text=True)
        if tree is None:
            return []

        try:
            root = tree.getroot()

            if root is None:
                return []

            return self.detector.find_in_tree_return_list(root)
        except (etree.XMLSyntaxError, OSError) as exc:
            logger.error("Failed to parse %s: %s", path, exc)
            return []

    def _get_tree(
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
            return tree
        except (etree.XMLSyntaxError, OSError) as exc:
            logger.error(f"Failed to parse SVG file {path}: {exc}")
            return None

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
            tree = self._get_tree(src_path)
            if tree is None:
                return RepairResult(
                    success=False,
                    len_tags_before_fix=0,
                    len_tags_after_fix=0,
                    warnings=[f"Failed to parse source file: {src_path}"],
                )
            root = tree.getroot()

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
