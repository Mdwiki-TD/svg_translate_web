from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    count: int
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationResult:
    before: int
    after: int
    fixed: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


__all__ = [
    "DetectionResult",
    "VerificationResult",
]
