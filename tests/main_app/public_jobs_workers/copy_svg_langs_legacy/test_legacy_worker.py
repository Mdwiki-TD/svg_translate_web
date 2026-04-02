from pathlib import Path
from unittest.mock import MagicMock, patch

from src.main_app.public_jobs_workers.copy_svg_langs_legacy.worker import (
    copy_svg_langs_worker_entry,
)
