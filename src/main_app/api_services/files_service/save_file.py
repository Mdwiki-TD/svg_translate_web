from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class WriteData:
    path: Path
    success: bool | None = None
    error: str | None = None


def write_bytes_to_file(*, content: bytes, filename: str, output_dir: Path) -> WriteData:

    # Extract just the filename part (remove "File:" prefix if present)
    clean_filename = filename.removeprefix("File:")

    # Determine output path - maintain original filename
    out_path = output_dir / clean_filename
    try:
        out_path.write_bytes(content)
        return WriteData(
            success=True,
            path=out_path,
        )
    except Exception as e:
        logger.error(f"Failed to save: {str(out_path)} -> {e}")
        return WriteData(
            success=False,
            path=out_path,
            error=str(e),
        )


__all__ = [
    "write_bytes_to_file",
]
