from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DiffResult:
    added: dict[str, dict[str, str]] = field(default_factory=dict)
    removed: dict[str, dict[str, str]] = field(default_factory=dict)
    changed: dict[str, dict[str, Any]] = field(default_factory=dict)
    target_changed: bool = False

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def to_json(self) -> dict[str, Any]:
        data = asdict(self)  # pyright: ignore[reportCallIssue]
        data["has_changes"] = self.has_changes
        return data

    @classmethod
    def compute_diff(cls, before: dict[str, Any], after: dict[str, Any]) -> DiffResult:
        """Compare two translations dicts and return added/removed/changed entries.

        Compares the ``"new"`` section of each translations dict.

        Args:
            before: Translations dict extracted before injection.
            after: Translations dict extracted after injection.

        Returns:
            DiffResult with added, removed, and changed entries.
        """
        before_new: dict[str, dict[str, str]] = before.get("new", {})
        after_new: dict[str, dict[str, str]] = after.get("new", {})

        before_keys = set(before_new.keys())
        after_keys = set(after_new.keys())

        added = {k: after_new[k] for k in sorted(after_keys - before_keys)}
        removed = {k: before_new[k] for k in sorted(before_keys - after_keys)}

        changed: dict[str, dict[str, Any]] = {}
        for key in sorted(before_keys & after_keys):
            if before_new[key] != after_new[key]:
                changed[key] = {
                    "before": before_new[key],
                    "after": after_new[key],
                }

        return cls(added=added, removed=removed, changed=changed)  # pyright: ignore[reportCallIssue]


__all__ = [
    "DiffResult",
]
