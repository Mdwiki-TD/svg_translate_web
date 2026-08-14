from __future__ import annotations

import logging
from pathlib import Path

from CopySVGTranslation import NestedTspanDetector, NestedTspanFlattener  # type: ignore
from lxml import etree

from ..fix_nested.objects import DetectionResult, VerificationResult

logger = logging.getLogger(__name__)


class MatchFixNestedTags:
    def __init__(
        self,
        source_file: Path | str,
        new_path: Path | str,
        pretty_print: bool | None = None,
    ) -> None:
        self.source_file = Path(source_file)
        self.new_path = Path(new_path)

        self.len_tags_before_fix = 0
        self.pretty_print = pretty_print
        self.flattener = NestedTspanFlattener(strategy="flatten", also_fix_a=True)
        self.detector = NestedTspanDetector()

    def _flatten_all(self, root):
        # Process nested tspans using Flattener
        self.flattener.process(root)
        return root

    def _get_root(self):
        parser = etree.XMLParser(remove_blank_text=False)
        # ---
        try:
            tree = etree.parse(str(self.source_file), parser)
        except (etree.XMLSyntaxError, OSError) as exc:
            logger.error(f"Failed to parse SVG file {self.source_file}: {exc}")
            return None
        # ---
        root = tree.getroot()
        return root

    def _save_file(self, root: etree.Element) -> None:
        _str = etree.tostring(
            root,
            encoding="unicode",
            pretty_print=self.pretty_print,
        )  # pyright: ignore[reportCallIssue]

        self.new_path.write_text(_str, encoding="utf-8")

    def match_nested(self) -> list:
        return self.detector.find_in_file(self.source_file)

    def fix_file(self) -> bool:
        # ---
        root = self._get_root()
        # ---
        if root is None:
            return False
        # ---
        self.len_tags_before_fix = len(self.detector.find_in_tree(root))
        # ---
        root = self._flatten_all(root)
        # ---
        try:
            self._save_file(root)
            return True
        except Exception:
            logger.error(f"Failed to write fixed svg file to: {str(self.new_path)}")
        # ---
        return False

    def verify_after_fix(self) -> VerificationResult:
        """Verify nested tags count after fix."""
        after = self.match_nested()
        after_count = len(after)
        return VerificationResult(
            before=self.len_tags_before_fix,
            after=after_count,
            fixed=max(0, self.len_tags_before_fix - after_count),
        )

    def detect_nested_tags(self) -> DetectionResult:
        """Detect nested tags in SVG file."""
        nested = self.match_nested()
        return DetectionResult(
            count=len(nested),
            tags=nested,
        )


__all__ = [
    "MatchFixNestedTags",
]
