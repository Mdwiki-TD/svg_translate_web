"""Unit tests for copy_svg_langs objects module."""

from __future__ import annotations

from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.objects import (
    CopySvgLangsWorkerObject,
    FilesProcessedItem,
    FileSteps,
    StageDetail,
    Stages,
    StepResult,
)


class TestStageDetail:
    def test_defaults(self):
        s = StageDetail()
        assert s.name == ""
        assert s.status == "pending"
        assert s.message == ""
        assert s.data is None

    def test_custom_values(self):
        s = StageDetail(name="x", status="Done", message="ok", data={"k": 1})
        assert s.name == "x"
        assert s.data == {"k": 1}


class TestStages:
    def test_default_stage_names(self):
        stages = Stages()
        assert stages.text.name == "text"
        assert stages.titles.name == "titles"
        assert stages.translations.name == "translations"


class TestStepResult:
    def test_defaults(self):
        r = StepResult()
        assert r.result is None
        assert r.msg == ""


class TestFileSteps:
    def test_defaults(self):
        fs = FileSteps()
        assert fs.download.result is None
        assert fs.nested.result is None
        assert fs.inject.result is None
        assert fs.upload.result is None


class TestFilesProcessedItem:
    def test_defaults(self):
        item = FilesProcessedItem(title="File.svg")
        assert item.title == "File.svg"
        assert item.status == "pending"
        assert item.error is None
        assert isinstance(item.steps, FileSteps)


class TestCopySvgLangsWorkerObject:
    def test_defaults(self):
        obj = CopySvgLangsWorkerObject()
        assert obj.job_id == 0
        assert obj.note == ""
        assert obj.args == {}
        assert obj.title is None
        assert isinstance(obj.stages, Stages)

    def test_to_json(self):
        obj = CopySvgLangsWorkerObject()
        obj.job_id = 42
        obj.title = "Test.svg"
        data = obj.to_json()
        assert isinstance(data, dict)
        assert data["job_id"] == 42
        assert data["title"] == "Test.svg"
        assert "stages" in data
        assert "files_processed" in data
