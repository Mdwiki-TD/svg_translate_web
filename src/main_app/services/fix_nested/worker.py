from __future__ import annotations

import logging
from pathlib import Path

from ..copysvg_wrapper import MatchFixNestedTags
from .objects import DetectionResult, VerificationResult

logger = logging.getLogger(__name__)


def detect_nested_tags(file_path: Path) -> DetectionResult:
    """Detect nested tags in SVG file."""
    processer = MatchFixNestedTags(
        pretty_print=True,
        source_file=file_path,
        new_path=file_path,
    )
    nested = processer.match_nested()
    return DetectionResult(
        count=len(nested),
        tags=nested,
    )


def fix_nested_tags(file_path: Path) -> bool:
    """Fix nested tags in-place."""
    logger.info("Fixing nested tags in: %s", file_path.name)
    processer = MatchFixNestedTags(
        pretty_print=True,
        source_file=file_path,
        new_path=file_path,
    )
    return processer.fix_file()


def verify_fix(file_path: Path, before_count: int) -> VerificationResult:
    """Verify nested tags count after fix."""
    processer = MatchFixNestedTags(
        pretty_print=True,
        source_file=file_path,
        new_path=file_path,
    )

    return processer.verify_after_fix(before_count)


__all__ = [
    "detect_nested_tags",
    "fix_nested_tags",
    "verify_fix",
]
