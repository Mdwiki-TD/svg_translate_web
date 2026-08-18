from __future__ import annotations

import pytest

from src.main_app.api_services.files_service.objects import FileData

# ══════════════════════════════════════════════════════════════════════════════
# Fixtures & Helpers
# ══════════════════════════════════════════════════════════════════════════════


class TestFixFileName:
    @pytest.mark.parametrize(
        "input_name, expected",
        [
            ("file:Test.jpg", "Test.jpg"),
            ("File:Test.jpg", "Test.jpg"),
            ("FILE:Test.jpg", "Test.jpg"),
            ("  Test.jpg  ", "Test.jpg"),
            ("Test.jpg", "Test.jpg"),
        ],
    )
    def test_filename_cleaning(self, input_name, expected, tmp_path):
        data = FileData.from_dict(file_name=input_name, file_path=tmp_path / "test.jpg")
        assert data.file_name == expected

    def test_none_file_name_not_processed(self, tmp_path):
        data = FileData.from_dict(file_name=None, file_path=tmp_path / "test.jpg")
        assert data.file_name is None
