"""Objects for add_svglanguages_template worker."""

from __future__ import annotations

from dataclasses import dataclass

from ...shared_objects import StandardAdminWorkerObject


@dataclass
class AddSvgLanguagesWorkerObject(StandardAdminWorkerObject):
    pass


__all__ = [
    "AddSvgLanguagesWorkerObject",
]
