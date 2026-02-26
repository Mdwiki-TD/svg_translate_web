"""Base worker infrastructure with standardized lifecycle management."""

from __future__ import annotations

import functools
import logging
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, Final, TypeVar

from . import jobs_service
from .utils import generate_result_file_name

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def job_exception_handler(
    result_file: str,
    job_id: int,
    job_type: str,
) -> Callable[[F], F]:
    """Decorator that wraps job execution with standardized exception handling.

    This decorator provides:
    - Exception catching and logging
    - Automatic result saving on failure
    - Job status updates on failure

    Args:
        result_file: The name of the result file to save
        job_id: The job ID for logging and status updates
        job_type: The type of job for status updates

    Returns:
        Decorated function with exception handling
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Job {job_id}: Fatal error during {func.__name__}")

                # Save error result
                error_result = {
                    "job_id": job_id,
                    "completed_at": datetime.now().isoformat(),
                    "error": str(e),
                    "error_type": type(e).__name__,
                }

                try:
                    jobs_service.save_job_result_by_name(result_file, error_result)
                    jobs_service.update_job_status(
                        job_id, "failed", result_file, job_type=job_type
                    )
                except LookupError:
                    logger.warning(
                        f"Job {job_id}: Could not update status to failed, "
                        "job record might have been deleted."
                    )
                except Exception:
                    logger.exception(f"Job {job_id}: Failed to save error result")
                    try:
                        jobs_service.update_job_status(
                            job_id, "failed", job_type=job_type
                        )
                    except LookupError:
                        pass

                return None

        return wrapper  # type: ignore[return-value]

    return decorator


class BaseJobWorker(ABC):
    """Abstract base class for job workers with standardized lifecycle.

    This base class provides:
    - Standardized result structure initialization
    - Lifecycle management (start, run, finalize)
    - Exception handling at the worker level
    - Automatic job status updates
    - Result file generation and saving

    Subclasses must implement:
    - get_job_type(): Return the job type string
    - get_initial_result(): Return the initial result dictionary
    - process(): Implement the actual processing logic

    Optional overrides:
    - before_run(): Called before processing starts
    - after_run(): Called after processing completes
    """

    def __init__(
        self,
        job_id: int,
        user: Dict[str, Any] | None = None,
        cancel_event: threading.Event | None = None,
    ):
        self.job_id: Final[int] = job_id
        self.user: Final[Dict[str, Any] | None] = user
        self.cancel_event: Final[threading.Event | None] = cancel_event
        self.job_type: str = self.get_job_type()
        self.result_file: str = generate_result_file_name(job_id, self.job_type)
        self.result: Dict[str, Any] = self.get_initial_result()
        self._status: str = "pending"

    @abstractmethod
    def get_job_type(self) -> str:
        """Return the job type string identifier.

        Returns:
            The job type string (e.g., 'crop_main_files', 'collect_main_files')
        """
        ...

    @abstractmethod
    def get_initial_result(self) -> Dict[str, Any]:
        """Return the initial result dictionary structure.

        Returns:
            Dictionary with initial result structure including
            job_id, started_at, summary, and tracking lists
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
            jobs_service.update_job_status(
                self.job_id, "running", self.result_file, job_type=self.job_type
            )
            return True
        except LookupError:
            logger.warning(
                f"Job {self.job_id}: Could not update status to running, "
                "job record might have been deleted."
            )
            return False

    def after_run(self) -> None:
        """Called after processing completes (success or failure)."""
        # Finalize timestamps
        self.result["completed_at"] = datetime.now().isoformat()
        final_status = self.result.get("status", "completed")

        # Save final results
        try:
            jobs_service.save_job_result_by_name(self.result_file, self.result)
        except Exception:
            logger.exception(f"Job {self.job_id}: Failed to save job result")

        # Update final status
        try:
            jobs_service.update_job_status(
                self.job_id, final_status, self.result_file, job_type=self.job_type
            )
        except LookupError:
            logger.warning(
                f"Job {self.job_id}: Could not update final status, "
                "job record might have been deleted."
            )

        logger.info(f"Job {self.job_id}: Finished with status {final_status}")

    def is_cancelled(self) -> bool:
        """Check if the job has been cancelled.

        Returns:
            True if cancelled, False otherwise
        """
        if self.cancel_event and self.cancel_event.is_set():
            self.result["status"] = "cancelled"
            self.result["cancelled_at"] = datetime.now().isoformat()
            return True
        return False

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

        self.result["status"] = "failed"
        self.result["error"] = str(error)
        self.result["error_type"] = type(error).__name__

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
                return self.result

            # Main processing
            self.result = self.process()

        except Exception as e:
            self.handle_error(e)

        finally:
            # Post-processing cleanup
            self.after_run()

        return self.result


__all__ = [
    "BaseJobWorker",
    "job_exception_handler",
]
