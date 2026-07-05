"""
conftest for unit tests
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

# ── jobs_workers fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch, mock_base_worker):
    """Mock the services used by fix_nested_jobs worker."""

    mocks = {
        "save_job_result_by_name": MagicMock(),
        "download_svg_file": MagicMock(),
        "detect_nested_tags": MagicMock(),
        "fix_nested_tags": MagicMock(),
        "verify_fix": MagicMock(),
        "upload_fixed_svg": MagicMock(),
        "is_job_cancelled": MagicMock(),
    }

    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.save_job_result_by_name",
        mocks["save_job_result_by_name"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker.download_svg_file",
        mocks["download_svg_file"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker.detect_nested_tags",
        mocks["detect_nested_tags"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker.fix_nested_tags",
        mocks["fix_nested_tags"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker.verify_fix",
        mocks["verify_fix"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker.upload_fixed_svg",
        mocks["upload_fixed_svg"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.is_job_cancelled",
        mocks["is_job_cancelled"],
    )

    return mocks
