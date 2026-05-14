from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class JobRecord:
    """Representation of a background job."""

    id: int
    job_type: str
    status: str  # pending, running, completed, failed
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result_file: str | None = None  # Path to JSON file with job results
    created_at: datetime | None = None
    updated_at: datetime | None = None
    username: str | None = None  # User who started the job
