"""Unit tests for db_CreateUpdate module."""

from __future__ import annotations

import logging
from unittest.mock import Mock

import pytest

from src.main_app.db.copy_svg_langs_db.db_CreateUpdate import CreateUpdateTask, TaskAlreadyExistsError


def test_task_already_exists_error_stores_task():
    """Test TaskAlreadyExistsError stores the conflicting task."""
    conflicting_task = {"id": "task123", "title": "Test"}

    error = TaskAlreadyExistsError(conflicting_task)

    assert error.task == conflicting_task
    assert "Task with this title is already in progress" in str(error)
