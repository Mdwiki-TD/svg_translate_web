"""Server-side session workspace for the interactive translate workflow.

Each session caches the downloaded SVG on disk and store the extracted mapping
plus metadata so the edit form can be rendered without re-downloading or
re-parsing the file.
"""

from __future__ import annotations

import json
import logging
import shutil
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .mapping import ExtractorData

logger = logging.getLogger(__name__)

_SESSIONS_DIR_NAME = "translate_sessions"
_SESSION_FILE = "session.json"
_SVG_FILE = "source.svg"
_OUTPUT_FILE = "output.svg"


@dataclass
class TranslateSession:
    """Persistent workspace for one interactive-translate session.

    Attributes:
        session_id: Unique identifier (UUID hex).
        source_type: ``"commons"`` or ``"upload"``.
        commons_title: Commons file title (when ``source_type == "commons"``).
        upload_filename: Original filename (when ``source_type == "upload"``).
        mapping_json: Serialized ``ExtractorData.to_json()`` dict.
        created_at: ISO-8601 timestamp.
    """

    session_id: str = ""
    source_type: str = "commons"
    commons_title: str = ""
    upload_filename: str = ""
    mapping_json: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sessions_root(base_dir: Path) -> Path:
        root = base_dir / _SESSIONS_DIR_NAME
        root.mkdir(parents=True, exist_ok=True)
        return root

    def session_dir(self, base_dir: Path) -> Path:
        return self._sessions_root(base_dir) / self.session_id

    def svg_path(self, base_dir: Path) -> Path:
        return self.session_dir(base_dir) / _SVG_FILE

    def output_path(self, base_dir: Path) -> Path:
        return self.session_dir(base_dir) / _OUTPUT_FILE

    def _meta_path(self, base_dir: Path) -> Path:
        return self.session_dir(base_dir) / _SESSION_FILE

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, base_dir: Path) -> None:
        """Write session metadata to disk."""
        session_dir = self.session_dir(base_dir)
        session_dir.mkdir(parents=True, exist_ok=True)
        meta_path = self._meta_path(base_dir)
        meta_path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, session_id: str, base_dir: Path) -> TranslateSession | None:
        """Load an existing session from disk, or ``None`` if not found."""
        # Validate session_id format (prevent path traversal)
        if not session_id or not all(c in "0123456789abcdef-" for c in session_id):
            logger.warning("Invalid session_id: %s", session_id)
            return None

        meta_path = cls._sessions_root(base_dir) / session_id / _SESSION_FILE
        if not meta_path.exists():
            return None

        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
            return cls(**data)
        except (json.JSONDecodeError, TypeError, OSError):
            logger.exception("Failed to load session %s", session_id)
            return None

    def delete(self, base_dir: Path) -> None:
        """Remove session directory entirely."""
        session_dir = self.session_dir(base_dir)
        if session_dir.exists():
            shutil.rmtree(session_dir, ignore_errors=True)

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    def get_mapping(self) -> ExtractorData:
        """Reconstruct ``ExtractorData`` from stored JSON."""
        return ExtractorData.from_any(self.mapping_json)

    def set_mapping(self, mapping: ExtractorData) -> None:
        self.mapping_json = mapping.to_json()

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        *,
        source_type: str,
        commons_title: str = "",
        upload_filename: str = "",
        mapping: ExtractorData | None = None,
        created_at: str = "",
    ) -> TranslateSession:
        """Create a new session with a fresh UUID."""
        return cls(
            session_id=uuid.uuid4().hex,
            source_type=source_type,
            commons_title=commons_title,
            upload_filename=upload_filename,
            mapping_json=mapping.to_json() if mapping else {},
            created_at=created_at,
        )


def cleanup_old_sessions(base_dir: Path, max_age_hours: int = 24) -> int:
    """Remove session directories older than *max_age_hours*.

    Returns:
        Number of sessions removed.
    """
    sessions_root = base_dir / _SESSIONS_DIR_NAME
    if not sessions_root.exists():
        return 0

    cutoff = time.time() - (max_age_hours * 3600)
    removed = 0

    for session_dir in sessions_root.iterdir():
        if not session_dir.is_dir():
            continue
        meta = session_dir / _SESSION_FILE
        if not meta.exists():
            # Orphan directory — remove
            shutil.rmtree(session_dir, ignore_errors=True)
            removed += 1
            continue

        try:
            if meta.stat().st_mtime < cutoff:
                shutil.rmtree(session_dir, ignore_errors=True)
                removed += 1
        except OSError as exc:
            logger.debug("Failed to check/remove session %s: %s", session_dir.name, exc)

    if removed:
        logger.info("Cleaned up %d old translate sessions", removed)
    return removed


__all__ = [
    "TranslateSession",
    "cleanup_old_sessions",
]
