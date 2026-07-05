"""Unit tests for fix_nested_main_files worker module."""

from __future__ import annotations

from pathlib import Path

from src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files import worker
from src.main_app.shared.fix_nested.worker import (
    DetectionResult,
    VerificationResult,
)

def test_repair_nested_svg_tags_success(mock_fix_nested_services, tmp_path):
    """Test successful high-level orchestration for a single file."""
    filename = "Test.svg"
    user = {"username": "tester"}

    mock_fix_nested_services["download_svg_file"].return_value = {"ok": True, "path": Path("tmp/path.svg")}
    mock_fix_nested_services["detect_nested_tags"].return_value = DetectionResult(count=5)
    mock_fix_nested_services["fix_nested_tags"].return_value = True
    mock_fix_nested_services["verify_fix"].return_value = VerificationResult(before=5, after=0, fixed=5)
    mock_fix_nested_services["upload_fixed_svg"].return_value = {"ok": True, "result": {"newrevid": 123}}

    result = worker.repair_nested_svg_tags(filename, user, tmp_path)

    assert result["success"] is True
    assert "Successfully fixed 5 nested tag(s)" in result["message"]
    mock_fix_nested_services["upload_fixed_svg"].assert_called_once()


def test_repair_nested_svg_tags_no_tags(mock_fix_nested_services, tmp_path):
    """Test behavior when no nested tags are detected."""
    mock_fix_nested_services["download_svg_file"].return_value = {"ok": True, "path": Path("tmp/path.svg")}
    mock_fix_nested_services["detect_nested_tags"].return_value = DetectionResult(count=0)

    result = worker.repair_nested_svg_tags("Clean.svg", {}, tmp_path)

    assert result["success"] is False
    assert result["no_nested_tags"] is True
    assert "No nested tags found" in result["message"]
