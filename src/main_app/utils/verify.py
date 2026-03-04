"""
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List
logger = logging.getLogger(__name__)


def verify_required_fields(required_fields: Dict[str, Any]) -> List[str]:
    """
    Verify that all required fields in a dictionary have truthy values.

    Args:
        required_fields: A dictionary where keys are field names and values are the
            values to check.

    Returns:
        A list of field names that are missing (i.e., have falsy values like
        None, "", [], {}, 0, or False).
    """
    missing_fields = []
    for field, value in required_fields.items():
        if not value:
            logger.error(f"Missing required field: {field}")
            missing_fields.append(field)
    return missing_fields


__all__ = [
    "verify_required_fields",
]
