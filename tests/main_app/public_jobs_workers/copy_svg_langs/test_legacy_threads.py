"""Unit tests for task thread orchestration."""

import threading
import time

import pytest

from src.main_app import create_app
from src.main_app.public_jobs_workers.copy_svg_langs import legacy_run_task
from src.main_app.public_jobs_workers.copy_svg_langs.legacy_threads import (
    get_cancel_event,
    launch_task_thread,
)


def test_launch_thread_registers_and_cleans_cancel_event(monkeypatch):
    started = threading.Event()
    release = threading.Event()

    def fake_run_task(
        _db_data, _task_id, _title, _args, _user_payload, *, cancel_event=None
    ):  # pylint: disable=too-many-arguments
        # signal we started and wait briefly until released
        started.set()
        release.wait(timeout=0.2)

    # Patch the run_task imported in legacy_threads
    monkeypatch.setattr("src.main_app.public_jobs_workers.copy_svg_langs.legacy_threads.run_task", fake_run_task)

    # Create app and push context for thread launch
    app = create_app()
    task_id = "t-abc123"

    with app.app_context():
        launch_task_thread(task_id, "Title", args=SimpleNamespace(), user_payload={})

    # ensure registered
    assert started.wait(timeout=0.2), "Thread did not start in time"
    assert get_cancel_event(task_id) is not None

    # let thread exit; then cancel event entry should be removed
    release.set()
    # give a tiny bit of time for cleanup
    for _ in range(10):
        if get_cancel_event(task_id) is None:
            break
        time.sleep(0.02)
    assert get_cancel_event(task_id) is None


class SimpleNamespace:
    """Minimal args placeholder."""

    pass
