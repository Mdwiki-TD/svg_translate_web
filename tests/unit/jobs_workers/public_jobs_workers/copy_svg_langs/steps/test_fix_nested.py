from unittest.mock import patch

from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.fix_nested import fix_nested_step


@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.fix_nested.match_nested_tags")
@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.fix_nested.fix_nested_file")
def test_fix_nested_task_success(mock_fix, mock_match, tmp_path):
    mock_match.side_effect = [["tag1"], []]
    mock_fix.return_value = True

    files = {"file1.svg": str(tmp_path / "file1.svg")}

    result = fix_nested_step(files)

    assert result["success"] is True
    assert result["data"]["status"]["fixed"] == 1
    assert result["data"]["status"]["len_nested_files"] == 1
    assert result["summary"]["total"] == 1


@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.fix_nested.match_nested_tags")
def test_fix_nested_task_no_nested(mock_match, tmp_path):
    mock_match.return_value = []

    files = {"file1.svg": str(tmp_path / "file1.svg")}

    result = fix_nested_step(files)

    assert result["success"] is True
    assert result["data"]["status"]["len_nested_files"] == 0
    assert result["data"]["status"]["fixed"] == 0


@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.fix_nested.match_nested_tags")
def test_fix_nested_cancelled(tmp_path):
    files = {"file1.svg": str(tmp_path / "file1.svg"), "file2.svg": str(tmp_path / "file2.svg")}

    result = fix_nested_step(files, cancel_check=lambda: True)

    assert result["success"] is True
    assert result["summary"]["total"] == 2
    assert result["summary"]["nested"] == 0


@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.fix_nested.match_nested_tags")
def test_fix_nested_too_many_tags(tmp_path):
    mock_tags = [f"tag{i}" for i in range(11)]
    with patch(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.fix_nested.match_nested_tags",
        return_value=mock_tags,
    ):
        files = {"file1.svg": str(tmp_path / "file1.svg")}
        result = fix_nested_step(files)

    assert result["summary"]["not_fixed"] == 1
    assert result["summary"]["nested"] == 1
    assert result["data"]["status"]["not_fixed"] == 1


@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.fix_nested.match_nested_tags")
@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.fix_nested.fix_nested_file")
def test_fix_nested_partial_fix(mock_fix, mock_match, tmp_path):
    mock_match.side_effect = [["tag1", "tag2"], ["tag3"]]
    mock_fix.return_value = True

    files = {"file1.svg": str(tmp_path / "file1.svg")}
    result = fix_nested_step(files)

    assert result["summary"]["not_fixed"] == 1
    assert result["data"]["status"]["not_fixed"] == 1


@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.fix_nested.match_nested_tags")
@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.fix_nested.fix_nested_file")
def test_fix_nested_fix_fails(mock_fix, mock_match, tmp_path):
    mock_match.return_value = ["tag1"]
    mock_fix.return_value = False

    files = {"file1.svg": str(tmp_path / "file1.svg")}
    result = fix_nested_step(files)

    assert result["summary"]["not_fixed"] == 1
    assert result["data"]["status"]["not_fixed"] == 1


@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.fix_nested.match_nested_tags")
def test_fix_nested_progress_callback_no_nested(mock_match, tmp_path):
    mock_match.return_value = []
    progress_calls = []

    def progress_cb(index, total, msg, results):
        progress_calls.append({"index": index, "msg": msg})

    files = {f"file{i}.svg": str(tmp_path / f"file{i}.svg") for i in range(15)}
    fix_nested_step(files, progress_callback=progress_cb)

    assert len(progress_calls) >= 1


@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.fix_nested.match_nested_tags")
@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.fix_nested.fix_nested_file")
def test_fix_nested_progress_callback_with_nested(mock_fix, mock_match, tmp_path):
    mock_match.side_effect = [["tag1"], []]
    mock_fix.return_value = True
    progress_calls = []

    def progress_cb(index, total, msg, results):
        progress_calls.append({"index": index, "msg": msg})

    files = {"file1.svg": str(tmp_path / "file1.svg")}
    fix_nested_step(files, progress_callback=progress_cb)

    assert len(progress_calls) >= 1
    assert any("Fixed:" in c["msg"] for c in progress_calls)


@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.fix_nested.match_nested_tags")
def test_fix_nested_final_progress_callback(mock_match, tmp_path):
    mock_match.return_value = []
    progress_calls = []

    def progress_cb(index, total, msg, results):
        progress_calls.append({"index": index, "msg": msg})

    files = {"file1.svg": str(tmp_path / "file1.svg")}
    fix_nested_step(files, progress_callback=progress_cb)

    assert len(progress_calls) >= 1
