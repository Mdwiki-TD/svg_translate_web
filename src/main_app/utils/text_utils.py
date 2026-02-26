"""
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List
logger = logging.getLogger(__name__)


def ensure_file_prefix(file_name) -> str:
    if not file_name.startswith("File:"):
        file_name = "File:" + file_name
    return file_name


def verify_required_fields(required_fields: Dict[str, Any]) -> List[str]:
    """
    Verify that all required fields are present in the data dictionary.

    Args:
        data: The dictionary to check.
        required_fields: A list of required field names.
    Returns:

    """
    missing_fields = []
    for field, value in required_fields.items():
        if not value:
            logger.error(f"Missing required field: {field}")
            missing_fields.append(field)
    return missing_fields


__all__ = [
    "ensure_file_prefix",
    "verify_required_fields",
]
