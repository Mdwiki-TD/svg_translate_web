"""Unit tests for template_service module."""

from __future__ import annotations

import pytest

from src.main_app.db.exceptions import DuplicateRecordError
from src.main_app.db.services.template_service import TemplateService


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        self.service = TemplateService()


class TestListTemplates(TestSetup):
    """Test list_templates function."""

    def test_list_templates_empty(self):
        templates = self.service.list()
        assert templates == []

    def test_list_templates_returns_all(self):
        data1 = {"title": "Template 1", "main_file": "file1.svg"}
        data2 = {"title": "Template 2", "main_file": "file2.svg"}
        data3 = {"title": "Template 3", "main_file": "file3.svg"}
        self.service.add_template_data(data1)
        self.service.add_template_data(data2)
        self.service.add_template_data(data3)

        templates = self.service.list()

        assert len(templates) == 3
        assert templates[0].title == "Template 1"
        assert templates[1].title == "Template 2"
        assert templates[2].title == "Template 3"

    def test_list_templates_with_limit(self):
        self.service.add_template_data({"title": "A", "main_file": "a.svg"})
        self.service.add_template_data({"title": "B", "main_file": "b.svg"})
        self.service.add_template_data({"title": "C", "main_file": "c.svg"})

        result = self.service.list(limit=2)

        assert len(result) == 2


class TestDeleteTemplate(TestSetup):
    """Test self.service.delete function."""

    def test_delete_template_success(self):
        data = {"title": "To Delete", "main_file": "delete.svg"}
        record = self.service.add_template_data(data)
        assert record is not None

        result = self.service.delete(record.id)

        assert result is True
        assert len(self.service.list()) == 0

    def test_delete_template_not_found_raises_lookup_error(self):
        result = self.service.delete(999)
        assert result is False


class TestAddTemplate(TestSetup):
    """Test add_template_data function."""

    def test_template_record_dataclass_with_none_main_file(self):
        data = {"title": "No Oldest File", "main_file": ""}
        record = self.service.add_template_data(data)
        assert record is not None

        assert record.title == "No Oldest File"
        assert isinstance(record.main_file, str)

    def test_add_template_empty_title_raises_value_error(self):
        data = {
            "title": "",
            "main_file": "file.svg",
        }
        with pytest.raises(ValueError, match="Title is required"):
            self.service.add_template_data(data)

    def test_add_template_success(self):
        data = {
            "title": "Test Template",
            "main_file": "test.svg",
        }
        record = self.service.add_template_data(data)
        assert record is not None

        assert record.title == "Test Template"
        assert record.main_file == "test.svg"
        assert record.id > 0

    def test_add_template_duplicate_raises_value_error(self):
        data1 = {
            "title": "Duplicate",
            "main_file": "file1.svg",
        }
        self.service.add_template_data(data1)

        data2 = {
            "title": "Duplicate",
            "main_file": "file2.svg",
        }
        with pytest.raises(DuplicateRecordError, match="Template 'Duplicate' already exists"):
            self.service.add_template_data(data2)

    def test_add_template_commit_failure_raises_error(self, monkeypatch):
        from src.main_app.extensions import db

        def _fail_commit():
            raise RuntimeError("DB connection lost")

        monkeypatch.setattr(db.session, "commit", _fail_commit)

        data = {"title": "Fail", "main_file": "fail.svg"}
        with pytest.raises(RuntimeError, match="DB connection lost"):
            self.service.add_template_data(data)


class TestListTemplatesMismatchedYears(TestSetup):
    """Test list_templates_mismatched_years function."""

    def test_empty_when_no_templates(self):
        result = self.service.list_templates_mismatched_years()
        assert result == []

    def test_empty_when_all_match(self):
        self.service.add_template_data(
            {"title": "T1", "last_world_file": "chart,World,2024.svg", "last_world_year": 2024}
        )
        self.service.add_template_data(
            {"title": "T2", "last_world_file": "chart,World,2025.svg", "last_world_year": 2025}
        )

        result = self.service.list_templates_mismatched_years()

        assert result == []

    def test_returns_mismatched(self):
        self.service.add_template_data(
            {"title": "Match", "last_world_file": "chart,World,2024.svg", "last_world_year": 2024}
        )
        self.service.add_template_data(
            {"title": "Mismatch", "last_world_file": "old_file.svg", "last_world_year": 2024}
        )

        result = self.service.list_templates_mismatched_years()

        assert len(result) == 1
        assert result[0].title == "Mismatch"

    def test_skips_null_fields(self):
        self.service.add_template_data({"title": "Null Year", "last_world_file": "file.svg"})
        self.service.add_template_data({"title": "Null File", "last_world_year": 2024})

        result = self.service.list_templates_mismatched_years()

        assert result == []


class TestGetTemplate(TestSetup):
    """Test get_template function."""

    def test_returns_template_by_id(self):
        record = self.service.add_template_data({"title": "Test", "main_file": "test.svg"})
        assert record is not None

        result = self.service.get_template(record.id)

        assert result is not None
        assert result.id == record.id
        assert result.title == "Test"

    def test_returns_none_when_not_found(self):
        result = self.service.get_template(999)
        assert result is None


class TestGetTemplateByTitle(TestSetup):
    """Test get_template_by_title function."""

    def test_returns_template_by_title(self):
        self.service.add_template_data({"title": "Unique Title", "main_file": "file.svg"})

        result = self.service.get_template_by_title("Unique Title")

        assert result is not None
        assert result.title == "Unique Title"

    def test_returns_none_when_not_found(self):
        result = self.service.get_template_by_title("Non-existent")
        assert result is None


class TestUpdateTemplateData(TestSetup):
    """Test update_template_data function."""

    def test_update_fields_successfully(self):
        record = self.service.add_template_data({"title": "Original", "main_file": "original.svg"})
        assert record is not None

        updated = self.service.update_template_data(record.id, {"main_file": "updated.svg"})

        assert updated is not None
        assert updated.id == record.id
        assert updated.title == "Original"
        assert updated.main_file == "updated.svg"

    def test_returns_none_when_template_not_found(self):
        result = self.service.update_template_data(999, {"main_file": "new.svg"})
        assert result is None

    def test_ignores_none_values(self):
        record = self.service.add_template_data({"title": "Original", "main_file": "original.svg"})
        assert record is not None

        updated = self.service.update_template_data(record.id, {"main_file": None, "title": "New Title"})

        assert updated is not None
        assert updated.title == "New Title"
        assert updated.main_file == "original.svg"

    def test_ignores_unknown_attributes(self):
        record = self.service.add_template_data({"title": "Original", "main_file": "file.svg"})
        assert record is not None

        updated = self.service.update_template_data(record.id, {"nonexistent_field": "value"})

        assert updated is not None
        assert updated.title == "Original"

    def test_handles_file_prefix_stripping(self):
        record = self.service.add_template_data({"title": "Original", "main_file": "file.svg"})
        assert record is not None

        updated = self.service.update_template_data(record.id, {"main_file": "File:new_file.svg"})

        assert updated is not None
        assert updated.main_file == "new_file.svg"
