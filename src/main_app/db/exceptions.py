from __future__ import annotations

from typing import Any, Dict


class MaxUserConnectionsError(Exception):
    pass


class TaskAlreadyExistsError(Exception):
    """Raised when attempting to create a duplicate active task."""

    def __init__(self, task: Dict[str, Any]):
        """
        Initialize the exception with the conflicting task.

        Parameters:
            task (Dict[str, Any]): The existing active task that caused the conflict; stored on the exception as the `task` attribute.
        """
        super().__init__("Task with this title is already in progress")
        self.task = task
