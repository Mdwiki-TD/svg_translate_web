from __future__ import annotations

import logging

from CopySVGTranslation import NestedStructureService as NestedStructureServiceOrignal  # type: ignore

logger = logging.getLogger(__name__)


class NestedStructureService(NestedStructureServiceOrignal):
    """ """

    def __init__(
        self,
        strategy: str = "flatten",
        also_fix_a: bool = True,
    ) -> None:
        super().__init__(strategy=strategy, also_fix_a=also_fix_a)


__all__ = [
    "NestedStructureService",
]
