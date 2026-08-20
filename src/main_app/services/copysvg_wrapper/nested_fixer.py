from __future__ import annotations

import logging
from pathlib import Path

from CopySVGTranslation import NestedTspanDetector, NestedTspanFlattener  # type: ignore
from lxml import etree

from ..fix_nested.objects import DetectionResult, NestedStrategy, VerificationResult

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

    def verify_after_fix(
        self,
        source_file: Path | str,
        len_tags_before_fix: int,
    ) -> VerificationResult:
        """Verify nested tags count after fix."""
        after = self.match_nested(source_file)
        after_count = len(after)
        return VerificationResult(
            before=len_tags_before_fix,
            after=after_count,
            fixed=max(0, len_tags_before_fix - after_count),
        )

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
    ) -> bool:
        """
        Repair nested tags in a file and write the result to another file.
        """
        root = self._get_root(source)
        if root is None:
            return False

        root = self.flattener.process(root)

        save_path = output or source
        try:
            self._save_file(root, save_path)
            return True
        except Exception:
            logger.error(f"Failed to write fixed svg file to: {str(save_path)}")

        return False

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
