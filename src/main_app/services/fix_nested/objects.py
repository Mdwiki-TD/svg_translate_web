from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

logger = logging.getLogger(__name__)


NestedStrategy = Literal["split_nested_tspans", "preserve_style", "flatten", "raise"]


@dataclass(slots=True)
class RepairResult:
    """
    Statistics and results of a nested structure repair operation.
    """

    success: bool
    len_tags_before_fix: int
    len_tags_after_fix: int
    warnings: list[str] = field(default_factory=list)


@dataclass
class DetectionResult:
    count: int
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)  # pyright: ignore[reportCallIssue]


@dataclass
class VerificationResult:
    before: int
    after: int
    fixed: int

    def to_json(self) -> dict[str, Any]:
        return asdict(self)  # pyright: ignore[reportCallIssue]


__all__ = [
    "DetectionResult",
    "VerificationResult",
]
