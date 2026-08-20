from __future__ import annotations

import logging
from pathlib import Path

from ..copysvg_wrapper import MatchFixNestedTags
from .objects import DetectionResult, VerificationResult

logger = logging.getLogger(__name__)


def detect_nested_tags(file_path: Path) -> DetectionResult:
    """Detect nested tags in SVG file."""
    processer = MatchFixNestedTags(
        strategy="flatten",
    )
    return processer.detect_nested_tags(file_path)


def repair_file(file_path: Path) -> bool:
    """Fix nested tags in-place."""
    logger.info("Fixing nested tags in: %s", file_path.name)
    processer = MatchFixNestedTags(
        strategy="flatten",
    )
    return processer.repair_file(file_path)


def verify_fix(file_path: Path, before_count: int) -> VerificationResult:
    """Verify nested tags count after fix."""
    processer = MatchFixNestedTags(
        strategy="flatten",
    )

    return processer.verify_after_fix(file_path, before_count)


__all__ = [
    "detect_nested_tags",
    "repair_file",
    "verify_fix",
]
