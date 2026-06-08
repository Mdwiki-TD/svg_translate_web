"""Base worker infrastructure with standardized lifecycle management."""

from __future__ import annotations

import logging
import threading
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Final, List, Optional

from sqlalchemy.orm.exc import StaleDataError

from ..config import settings
from ..db.services import (
    is_job_cancelled,
    update_job_status,
)
from ..su_services import is_job_cancelled_file_exist, save_job_result_by_name
from .utils import generate_result_file_name

logger = logging.getLogger(__name__)

WorkerError = Dict[str, Any]


@dataclass
class WorkerObject:
    status: str = "pending"
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    cancelled_at: Optional[str] = None
    last_update: Optional[str] = ""
    failed_at: Optional[str] = None
    errors: List[WorkerError] = field(default_factory=list)
    error: Optional[str] = None
    error_type: Optional[str] = None

    def to_json(self) -> Dict[str, Any]:
        """
        Converts the dataclass instance back to its original dictionary format.
        """

        return asdict(self)


class BaseObjectsJobWorker(ABC):
    """Abstract base class for job workers with standardized lifecycle.

    This base class provides:
    - Standardized result structure initialization
    - Lifecycle management (start, run, finalize)
    - Exception handling at the worker level
    - Automatic job status updates
    - Result file generation and saving

    Subclasses must implement:
    - get_job_type(): Return the job type string
    - process(): Implement the actual processing logic

    Optional overrides:
    - before_run(): Called before processing starts
    - after_run(): Called after processing completes
    """

    def __init__(
        self,
        job_id: int,
        user: dict[str, Any],
        cancel_event: threading.Event | None = None,
    ) -> None:
        self.job_id: Final[int] = job_id
        self.user: Final[Dict[str, Any] | None] = user
        self.cancel_event: Final[threading.Event | None] = cancel_event
        self.job_type: str = self.get_job_type()
        self.result_file: str = generate_result_file_name(job_id, self.job_type)
        self._status: str = "pending"
        self.result_file_cancelled: str = f"{self.result_file}.cancelled"
        self._edit_count: int = 0

        self.result: WorkerObject = None

    @abstractmethod
    def get_job_type(self) -> str:
        """Return the job type string identifier.

        Returns:
            The job type string (e.g., 'crop_main_files', 'collect_templates_data')
        """
        ...

    @abstractmethod
    def process(self) -> Dict[str, Any]:
        """Execute the main processing logic.

        This method should contain the actual work of the job.
        It should check for cancellation via self.cancel_event periodically.

        Returns:
            The populated result dictionary
        """
        ...

    def before_run(self) -> bool:
        """Called before processing starts.

        Returns:
            True to continue with processing, False to abort
        """
        try:
            update_job_status(self.job_id, "running", self.result_file, job_type=self.job_type)
            self.result.status = "running"
            self._save_progress()
            return True
        except LookupError:
            logger.exception(
                f"Job {self.job_id}: Could not update status to running, job record might have been deleted."
            )
            return False

    def after_run(self) -> None:
        """Called after processing completes (success or failure)."""
        # Finalize timestamps
        self.result.completed_at = datetime.now().isoformat()
        final_status = self.result.status or "completed"

        if final_status in ["running", "pending"]:
            final_status = "completed"

        self.result.status = final_status

        # Save final results
        self._save_progress()

        # Update final status
        try:
            update_job_status(self.job_id, final_status, self.result_file, job_type=self.job_type)
        except (StaleDataError, LookupError):
            logger.error(f"Job {self.job_id}: Could not update final status, job record might have been deleted.")
        except Exception:
            logger.error(f"Job {self.job_id}: Failed to update final status")

        logger.info(f"Job {self.job_id}: Finished with status {final_status}")

    def _save_progress(self, insert_last_update: bool = True) -> None:
        if insert_last_update:
            self.result.last_update = datetime.now().isoformat()
        result = self.result.to_json()
        try:
            save_job_result_by_name(self.result_file, result)
        except Exception:
            logger.exception(f"Job {self.job_id}: Failed to save job result")

    def is_cancelled(self, check_db: bool = False) -> bool:
        """Check if the job has been cancelled.

        Returns:
            True if cancelled, False otherwise
        """
        if self.cancel_event and self.cancel_event.is_set():
            logger.info(f"Job {self.job_id}: Local cancellation detected, stopping.")
            self._mark_as_cancelled_in_result()
            return True

        if is_job_cancelled_file_exist(self.result_file_cancelled):
            logger.info(f"Job {self.job_id}: Cancelled file detected, stopping.")
            self._mark_as_cancelled_in_result()
            return True

        if check_db:
            # Optimize is_cancelled DB check frequency, by reducing the check frequency (to occur every N cycles).
            if is_job_cancelled(self.job_id, job_type=self.job_type):
                logger.info(f"Job {self.job_id}: Global cancellation detected, stopping.")
                self._mark_as_cancelled_in_result()
                return True

        return False

    def check_cancel_db_periodic(self, interval: int = 10) -> bool:
        """
        Increment edit counter and check DB cancellation every `interval` edits.

        Call this after a successful edit (when outcome.newrevid exists)
        to periodically verify if an admin cancelled the job via the DB.

        Args:
            interval: Check DB every N successful edits (default 10).

        Returns:
            True if cancelled, False otherwise.
        """
        self._edit_count += 1
        if self._edit_count % interval == 0:
            return self.is_cancelled(check_db=True)
        return False

    def _mark_as_cancelled_in_result(self) -> None:
        """Standardize the result dictionary for a cancelled job."""
        self.result.status = "cancelled"
        if self.result.cancelled_at is None:
            self.result.cancelled_at = datetime.now().isoformat()
        self._save_progress(insert_last_update=False)

    def get_priority(self, length) -> int:
        if length < 11:
            return 1

        if settings.jobs.priority_per_item is not None:
            return settings.jobs.priority_per_item

        # Calculate the interval for progress updates to aim for about 10 updates.
        return min(10, length // 10)

    def handle_error(self, error: Exception, context: str = "") -> None:
        """Handle an error during processing.

        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
        """
        prefix = f"Job {self.job_id}"
        if context:
            prefix += f": {context}"
        logger.exception(prefix)

        self.result.status = "failed"
        self.result.failed_at = datetime.now().isoformat()

        self.log_errors(str(error), type(error).__name__)

    def log_errors(self, error: str, error_type: str = "") -> None:
        """ """
        if error:
            self.result.errors.append({"error": error, "error_type": error_type})

    def log_no_site_error(self) -> None:
        """ """
        self.result.status = "failed"
        self.result.failed_at = datetime.now().isoformat()
        self.log_errors("No authenticated user site available.")

    def run(self) -> Dict[str, Any]:
        """Execute the complete job lifecycle.

        This method orchestrates the entire job lifecycle:
        1. Calls before_run() to set up
        2. Calls process() to do the work
        3. Calls after_run() to clean up

        Returns:
            The final result dictionary
        """
        try:
            # Pre-processing setup
            if not self.before_run():
                return self.result.to_json()

            # Main processing
            self.result = self.process()

        except Exception as e:
            self.handle_error(e)

        finally:
            # Post-processing cleanup
            self.after_run()

        return self.result.to_json()


__all__ = [
    "BaseObjectsJobWorker",
]
