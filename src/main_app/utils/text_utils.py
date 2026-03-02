"""
"""

from __future__ import annotations


def ensure_file_prefix(file_name) -> str:
    if not file_name.startswith("File:"):
        file_name = "File:" + file_name
    return file_name


__all__ = [
    "ensure_file_prefix",
]
