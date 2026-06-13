"""Unit tests for shared fix_nested worker functions."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from src.main_app.shared.fix_nested.worker import (
    detect_nested_tags,
    fix_nested_tags,
    verify_fix,
)


@pytest.fixture
def mock_copy_svg():
    with (
        patch("src.main_app.shared.fix_nested.worker.match_nested_tags") as m_match,
        patch("src.main_app.shared.fix_nested.worker.fix_nested_file") as m_fix,
    ):
        yield {"match": m_match, "fix": m_fix}

def test_detect_nested_tags(mock_copy_svg):
    mock_copy_svg["match"].return_value = ["tag1", "tag2"]
    res = detect_nested_tags(Path("test.svg"))
    assert res.count == 2
    assert res.tags == ["tag1", "tag2"]


def test_fix_nested_tags(mock_copy_svg):
    mock_copy_svg["fix"].return_value = True
    assert fix_nested_tags(Path("test.svg")) is True


def test_verify_fix(mock_copy_svg):
    mock_copy_svg["match"].return_value = ["tag1"]
    res = verify_fix(Path("test.svg"), before_count=3)
    assert res.before == 3
    assert res.after == 1
    assert res.fixed == 2
