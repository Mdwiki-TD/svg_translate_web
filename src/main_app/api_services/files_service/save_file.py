from __future__ import annotations

import logging
from pathlib import Path

from .objects import WriteData

logger = logging.getLogger(__name__)


def write_bytes_to_file(*, content: bytes, filename: str, output_dir: Path) -> WriteData:
    # Extract just the filename part (remove "File:" prefix if present)
    clean_filename = Path(filename.removeprefix("File:")).name

    if not clean_filename or clean_filename in {".", ".."}:
        return WriteData(success=False, path=output_dir, error="Invalid file name")

    # Determine output path - maintain original filename
    out_path = output_dir / clean_filename
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
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
