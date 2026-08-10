from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.main_app.api_services.files_service.service import (
    _upload_fixed_svg,
)

# ══════════════════════════════════════════════════════════════════════════════
# Fixtures & Helpers
# ══════════════════════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def mock_sleep(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock = MagicMock()
    monkeypatch.setattr(
        "src.main_app.api_services.files_service.upload_bot.time.sleep",
        _mock,
    )
    return _mock


class TestUploadFixedSvg:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch: pytest.MonkeyPatch):
        self.mock_up = MagicMock()
        monkeypatch.setattr(
            "src.main_app.api_services.files_service.upload_bot.UploadFile.upload",
            self.mock_up,
        )

    def test_upload_fixed_svg_no_user(self, mock_site):
        res = _upload_fixed_svg("Test.svg", Path("testzzz.svg"), mock_site, "")
        assert res.get("ok") is False

    def test_upload_fixed_svg_success(self, mock_site):
        self.mock_up.return_value = {"result": "success", "newrevid": 123}
        res = _upload_fixed_svg("Test.svg", Path("test.svg"), mock_site, "")
        assert res.get("ok") is True

    def test_upload_fixed_svg_fail(self, mock_site):
        self.mock_up.return_value = {"result": "Failure", "error": "ratelimited"}
        res = _upload_fixed_svg("Test.svg", Path("test.svg"), mock_site, "")
        assert res.get("ok") is False
        assert res.get("error") == "ratelimited"
