"""
Unit tests for src/main_app/jobs_workers/admin_jobs_workers/crop_main_files/objects.py module.
"""

from src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.objects import (
    CropFileProcessingInfo,
    CropFileSteps,
    CropMainFilesSummary,
    CropMainFilesWorkerObject,
    FileStep,
)


def test_file_step_defaults():
    step = FileStep()
    assert step.result is None
    assert step.msg == ""
    assert step.newrevid is None


def test_crop_file_steps_defaults():
    steps = CropFileSteps()
    assert isinstance(steps.download, FileStep)
    assert isinstance(steps.crop, FileStep)
    assert isinstance(steps.upload_cropped, FileStep)
    assert isinstance(steps.update_original, FileStep)
    assert isinstance(steps.update_template, FileStep)
    assert isinstance(steps.update_page, FileStep)
    assert isinstance(steps.update_cropped, FileStep)


def test_crop_file_processing_info_to_dict(tmp_path):
    info = CropFileProcessingInfo(
        template_id=1,
        template_title="Template:Test",
        original_file="File:test.svg",
        cropped_filename="File:test (cropped).svg",
        downloaded_path=tmp_path / "download.svg",
        cropped_path=tmp_path / "crop.svg",
    )
    info.steps.download.result = True
    info.steps.download.msg = "Downloaded"

    d = info.to_json()

    assert d["template_id"] == 1
    assert d["downloaded_path"] == str(tmp_path / "download.svg")
    assert d["cropped_path"] == str(tmp_path / "crop.svg")
    assert d["steps"]["download"] == {"result": True, "msg": "Downloaded", "newrevid": None}
    assert d["steps"]["crop"] == {"result": None, "msg": "", "newrevid": None}


def test_crop_main_files_summary_defaults():
    summary = CropMainFilesSummary()
    assert summary.total == 0
    assert summary.processed == 0
    assert summary.cropped == 0
    assert summary.uploaded == 0
    assert summary.updated == 0
    assert summary.skipped == 0
    assert summary.failed == 0


def test_crop_main_files_worker_object_defaults():
    obj = CropMainFilesWorkerObject(job_id=10)
    assert obj.job_id == 10
    assert isinstance(obj.summary, CropMainFilesSummary)
    assert obj.pages_to_work == []
    assert obj.pages_processed == []
