from unittest.mock import MagicMock, patch

import pytest

from src.main_app.public_jobs_workers.copy_svg_langs.steps.upload import upload_step


@pytest.fixture
def mock_site():
    return MagicMock()


@pytest.fixture
def mock_store():
    return MagicMock()


@patch("src.main_app.public_jobs_workers.copy_svg_langs.steps.uploads.up.build_upload_site")
def test_upload_task_disabled(mock_build, mock_store):
    stages = {}
    res, final_stages = upload_step(stages, {}, "Main", do_upload=False, store=mock_store)
    assert res["skipped"] is True
    assert final_stages["status"] == "Skipped"


@patch("src.main_app.public_jobs_workers.copy_svg_langs.steps.uploads.up.build_upload_site")
def test_upload_task_no_files(mock_build, mock_store):
    stages = {}
    res, final_stages = upload_step(stages, {}, "Main", do_upload=True, store=mock_store)
    assert res["skipped"] is True
    assert res["reason"] == "no-input"


@patch("src.main_app.public_jobs_workers.copy_svg_langs.steps.uploads.up.build_upload_site")
@patch("src.main_app.public_jobs_workers.copy_svg_langs.steps.uploads.up.mark_token_used")
def test_upload_task_success(mock_mark, mock_start, mock_build, mock_store):
    mock_build.return_value = MagicMock()
    mock_start.return_value = ({"done": 1}, {"status": "Completed"})

    stages = {}
    user = {"access_token": "token", "access_secret": "secret", "id": 123}
    files = {"f1": {"new_languages": 1}}

    res, final_stages = upload_step(
        stages, files, "Main", do_upload=True, user=user, store=mock_store, task_id="t1", check_cancel=lambda x: False
    )

    assert res["done"] == 1
    mock_mark.assert_called_with(123)
    mock_start.assert_called()
