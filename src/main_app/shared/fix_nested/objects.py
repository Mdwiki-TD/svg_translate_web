"""Objects for shared fix_nested worker."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class DownloadResult:
    ok: bool
    path: Optional[Path] = None
    error: Optional[str] = None
    details: Optional[dict[str, Any]] = None


@dataclass
class DetectionResult:
    count: int
    tags: list[str] = field(default_factory=list)


@dataclass
class VerificationResult:
    before: int
    after: int
    fixed: int


__all__ = [
    "DownloadResult",
    "DetectionResult",
    "VerificationResult",
]
