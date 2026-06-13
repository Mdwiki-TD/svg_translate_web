"""Objects for shared fix_nested worker."""

from __future__ import annotations

from dataclasses import dataclass, field


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
    "DetectionResult",
    "VerificationResult",
]
