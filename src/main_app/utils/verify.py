"""
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List
logger = logging.getLogger(__name__)


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
    "verify_required_fields",
]
