"""Unit tests for shared fix_nested worker functions."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.main_app.shared.fix_nested.worker import (
    detect_nested_tags,
    fix_nested_tags,
    verify_fix,
)

@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch):
    mocks = {
        "match": MagicMock(),
        "fix": MagicMock(),
    }
    monkeypatch.setattr(
        "src.main_app.shared.fix_nested.worker.match_nested_tags",
        mocks["match"],
    )
    monkeypatch.setattr(
        "src.main_app.shared.fix_nested.worker.fix_nested_file",
        mocks["fix"],
    )
    return mocks

def test_detect_nested_tags(mock_services):
    mock_services["match"].return_value = ["tag1", "tag2"]
    res = detect_nested_tags(Path("test.svg"))
    assert res.count == 2
    assert res.tags == ["tag1", "tag2"]


def test_fix_nested_tags(mock_services):
    mock_services["fix"].return_value = True
    assert fix_nested_tags(Path("test.svg")) is True


def test_verify_fix(mock_services):
    mock_services["match"].return_value = ["tag1"]
    res = verify_fix(Path("test.svg"), before_count=3)
    assert res.before == 3
    assert res.after == 1
    assert res.fixed == 2
