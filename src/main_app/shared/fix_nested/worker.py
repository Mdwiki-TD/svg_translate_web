from __future__ import annotations

import logging
from pathlib import Path

from CopySVGTranslation import fix_nested_file, match_nested_tags  # type: ignore

from .objects import (
    DetectionResult,
    VerificationResult,
)

logger = logging.getLogger(__name__)

def detect_nested_tags(file_path: Path) -> DetectionResult:
    """Detect nested tags in SVG file."""
    nested = match_nested_tags(str(file_path))
    return DetectionResult(
        count=len(nested),
        tags=nested,
    )


def fix_nested_tags(file_path: Path) -> bool:
    """Fix nested tags in-place."""
    logger.info(f"Fixing nested tags in: {file_path.name}")
    return bool(fix_nested_file(file_path, file_path))


def verify_fix(file_path: Path, before_count: int) -> VerificationResult:
    """Verify nested tags count after fix."""
    after = match_nested_tags(str(file_path))
    after_count = len(after)

    return VerificationResult(
        before=before_count,
        after=after_count,
        fixed=max(0, before_count - after_count),
    )

__all__ = [
    "detect_nested_tags",
    "fix_nested_tags",
    "verify_fix",
]
