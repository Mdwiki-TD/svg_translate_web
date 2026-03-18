"""

"""

from __future__ import annotations
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

json_files = Path(__file__).parent.glob('*.json')

data_list = {}

for file in json_files:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data_list[file.stem] = json.load(f)
    except Exception as e:
        logger.error(f'Error loading data from {file}: {e}')

__all__ = [
    "data_list",
]
