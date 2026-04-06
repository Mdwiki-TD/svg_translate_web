"""Unit tests for download step (no network)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.public_jobs_workers.copy_svg_langs.steps.download import download_step


class TestDownloadStep:
    @pytest.fixture
    def output_dir(self, tmp_path: Path) -> Path:
        return tmp_path / "downloads"

    @pytest.fixture
    def mock_success_result(self) -> dict:
        return {"result": "success", "path": "/path/to/file.svg", "msg": "Downloaded"}

    @pytest.fixture
    def mock_existing_result(self) -> dict:
        return {"result": "existing", "path": "/path/to/file.svg", "msg": "Skipped"}

    @pytest.fixture
    def mock_failure_result(self) -> dict:
        return {"result": "failed", "path": "", "msg": "Not found"}

    def test_download_step_success(
        self,
        output_dir: Path,
        mock_success_result: dict,
    ) -> None:
        with patch(
            "src.main_app.public_jobs_workers.copy_svg_langs.steps.download.download_one_file",
            return_value=mock_success_result,
        ):
            result = download_step(
                titles=["File:Test1.svg"],
                output_dir=output_dir,
            )

        assert result["success"] is True
        assert len(result["files"]) == 1
        assert result["summary"]["downloaded"] == 1
        assert result["summary"]["failed"] == 0

    def test_download_step_empty_titles(self, output_dir: Path) -> None:
        result = download_step(
            titles=[],
            output_dir=output_dir,
        )

        assert result["success"] is True
        assert result["files"] == []
        assert result["summary"]["total"] == 0

    def test_download_step_cancellation(self, output_dir: Path) -> None:
        cancel_called = False

        def cancel_check() -> bool:
            nonlocal cancel_called
            cancel_called = True
            return True

        with patch(
            "src.main_app.public_jobs_workers.copy_svg_langs.steps.download.download_one_file",
            return_value={"result": "success", "path": "/path", "msg": "ok"},
        ):
            result = download_step(
                titles=["File:A.svg", "File:B.svg"],
                output_dir=output_dir,
                cancel_check=cancel_check,
            )

        assert cancel_called
        assert result["success"] is False

    def test_download_step_skip_existing(
        self,
        output_dir: Path,
        mock_existing_result: dict,
    ) -> None:
        mock_existing_result["path"] = str(output_dir / "File_Existing.svg")
        with patch(
            "src.main_app.public_jobs_workers.copy_svg_langs.steps.download.download_one_file",
            return_value=mock_existing_result,
        ):
            result = download_step(
                titles=["File:Existing.svg"],
                output_dir=output_dir,
            )

        assert result["success"] is True
        assert result["summary"]["skipped_existing"] == 1
        assert "File:Existing.svg" in result["files_dict"]

    def test_download_step_failure(
        self,
        output_dir: Path,
        mock_failure_result: dict,
    ) -> None:
        with patch(
            "src.main_app.public_jobs_workers.copy_svg_langs.steps.download.download_one_file",
            return_value=mock_failure_result,
        ):
            result = download_step(
                titles=["File:Missing.svg"],
                output_dir=output_dir,
            )

        assert result["success"] is False
        assert result["summary"]["failed"] == 1
        assert "File:Missing.svg" in result["failed_titles"]

    def test_download_step_progress_callback(
        self,
        output_dir: Path,
        mock_success_result: dict,
    ) -> None:
        progress_calls: list = []

        def progress_callback(index: int, total: int, msg: str, results: dict) -> None:
            progress_calls.append({"index": index, "total": total, "msg": msg})

        with patch(
            "src.main_app.public_jobs_workers.copy_svg_langs.steps.download.download_one_file",
            return_value=mock_success_result,
        ):
            result = download_step(
                titles=[f"File:Test{i}.svg" for i in range(15)],
                output_dir=output_dir,
                progress_callback=progress_callback,
            )

        assert len(progress_calls) >= 1
        assert result["summary"]["downloaded"] == 15

    def test_download_step_creates_output_dir(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "new" / "nested" / "dir"

        with patch(
            "src.main_app.public_jobs_workers.copy_svg_langs.steps.download.download_one_file",
            return_value={"result": "success", "path": str(output_dir / "file.svg"), "msg": "ok"},
        ):
            download_step(titles=["File:Test.svg"], output_dir=output_dir)

        assert output_dir.exists()

    def test_download_step_multiple_files(
        self,
        output_dir: Path,
        mock_success_result: dict,
        mock_failure_result: dict,
    ) -> None:
        def mock_download(title: str, **kwargs: object) -> dict:
            if "Fail" in title:
                return {"result": "failed", "path": "", "msg": "Failed"}
            return {"result": "success", "path": f"/path/{title}", "msg": "ok"}

        with patch(
            "src.main_app.public_jobs_workers.copy_svg_langs.steps.download.download_one_file",
            side_effect=mock_download,
        ):
            result = download_step(
                titles=["File:Good1.svg", "File:Fail.svg", "File:Good2.svg"],
                output_dir=output_dir,
            )

        assert result["success"] is False
        assert result["summary"]["downloaded"] == 2
        assert result["summary"]["failed"] == 1
        assert len(result["failed_titles"]) == 1

    def test_download_step_with_session(self, output_dir: Path) -> None:
        mock_session = MagicMock()

        with patch(
            "src.main_app.public_jobs_workers.copy_svg_langs.steps.download.download_one_file",
            return_value={"result": "success", "path": "/path", "msg": "ok"},
        ) as mock_dl:
            download_step(
                titles=["File:Test.svg"],
                output_dir=output_dir,
                session=mock_session,
            )
            mock_dl.assert_called_once()
            _, kwargs = mock_dl.call_args
            assert kwargs["session"] is mock_session

    def test_download_step_overwrite_flag(self, output_dir: Path) -> None:
        with patch(
            "src.main_app.public_jobs_workers.copy_svg_langs.steps.download.download_one_file",
            return_value={"result": "success", "path": "/path", "msg": "ok"},
        ) as mock_dl:
            download_step(
                titles=["File:Test.svg"],
                output_dir=output_dir,
                overwrite_downloads=True,
            )
            _, kwargs = mock_dl.call_args
            assert kwargs["overwrite"] is True
