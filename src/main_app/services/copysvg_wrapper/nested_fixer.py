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
        self.flattener = NestedTspanFlattener(strategy=strategy, also_fix_a=also_fix_a)
        self.detector = NestedTspanDetector()

        self.root: etree._Element | None = None

    def _flatten_all(self, root):
        # Process nested tspans using Flattener
        self.flattener.process(root)
        return root

    def _get_root(self, source_file: Path | str):
        parser = etree.XMLParser(remove_blank_text=False)

        try:
            tree = etree.parse(str(source_file), parser)
        except (etree.XMLSyntaxError, OSError) as exc:
            logger.error(f"Failed to parse SVG file {source_file}: {exc}")
            return None

        self.root = tree.getroot()
        return self.root

    def _save_file(self, root: etree._Element, new_path: Path | str) -> None:
        _str = etree.tostring(
            root,
            encoding="unicode",
            pretty_print=None,
        )  # pyright: ignore[reportCallIssue]

        if not new_path:
            raise Exception("new_path is None")

        new_path = Path(new_path)
        new_path.write_text(_str, encoding="utf-8")

    def match_nested(self, source_file: Path | str) -> list[str]:
        root = self._get_root(source_file)
        if root is None:
            return []

        return self.detector.find_in_tree_return_list(root)

    def fix_file(self, source_file: Path | str, new_path: Path | str | None = None) -> bool:
        root = self._get_root(source_file)
        if root is None:
            return False

        root = self._flatten_all(root)

        save_path = new_path or source_file
        try:
            self._save_file(root, save_path)
            return True
        except Exception:
            logger.error(f"Failed to write fixed svg file to: {str(save_path)}")

        return False

    def verify_after_fix(self, source_file: Path | str, len_tags_before_fix: int) -> VerificationResult:
        """Verify nested tags count after fix."""
        after = self.match_nested(source_file)
        after_count = len(after)
        return VerificationResult(
            before=len_tags_before_fix,
            after=after_count,
            fixed=max(0, len_tags_before_fix - after_count),
        )

    def detect_nested_tags(self, source_file: Path | str) -> DetectionResult:
        """Detect nested tags in SVG file."""
        nested = self.match_nested(source_file)
        return DetectionResult(
            count=len(nested),
            tags=nested,
        )


__all__ = [
    "MatchFixNestedTags",
]
