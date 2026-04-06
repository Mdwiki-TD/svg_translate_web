"""
TODO: write tests for `src.main_app.public_jobs_workers.copy_svg_langs.service`
Unit tests for task thread orchestration.
"""

import threading
import time

import pytest

from src.main_app import create_app
from src.main_app.public_jobs_workers.copy_svg_langs.service import (
    get_cancel_event,
    start_copy_svg_langs_job,
)
