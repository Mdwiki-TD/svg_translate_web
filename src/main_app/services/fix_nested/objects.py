from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    before: int
    after: int
    fixed: int

    def to_json(self) -> dict[str, Any]:
        return asdict(self)  # pyright: ignore[reportCallIssue]


__all__ = [
    "VerificationResult",
]
