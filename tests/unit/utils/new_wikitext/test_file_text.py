import pytest
import wikitextparser as wtp

from src.main_app.utils.new_wikitext.file_text import (
    CroppedFileTextBuilder,
    InformationAuthorUpdater,
    OriginalFileTextUpdater,
)


def _wtp_works() -> bool:
    try:
        wtp.parse("a")
    except RuntimeError:
        return False
    return True


needs_wtp = pytest.mark.skipif(not _wtp_works(), reason="real wikitextparser is required")


class FakeInserter:
    def __init__(self):
        self.calls = []

    def insert_before_methods(self, text, block):
        self.calls.append((text, block))
        return "INSERTED"


class FakeOtherVersions:
    """Returns ``result`` (or the unchanged text when ``result`` is None)."""

    def __init__(self, result=None):
        self.result = result
        self.calls = []

    def add_template(self, text, template_name, value):
        self.calls.append((template_name, value))
        return text if self.result is None else self.result


class FakeAuthorUpdater:
    def update_information_author(self, text, author):
        return f"{text}|{author}"


class TestCroppedFileTextBuilder:
    """Tests for ``CroppedFileTextBuilder.create_cropped_file_text``."""

    def test_empty_text_returns_only_the_template(self):
        result = CroppedFileTextBuilder().create_cropped_file_text("File:A_b.svg", "  ")
        assert result == "{{Extracted from|1=A b.svg}}"

    def test_uses_other_versions_result(self):
        inserter = FakeInserter()
        builder = CroppedFileTextBuilder(inserter=inserter, other_versions=FakeOtherVersions("CHANGED"))
        assert builder.create_cropped_file_text("a.svg", "text") == "CHANGED"
        assert inserter.calls == []

    def test_falls_back_to_inserter(self):
        inserter = FakeInserter()
        builder = CroppedFileTextBuilder(inserter=inserter, other_versions=FakeOtherVersions())
        assert builder.create_cropped_file_text("a.svg", "text") == "INSERTED"
        assert inserter.calls == [("text", "{{Extracted from|1=a.svg}}")]

    def test_applies_author_citation(self):
        builder = CroppedFileTextBuilder(
            inserter=FakeInserter(),
            author_updater=FakeAuthorUpdater(),
            other_versions=FakeOtherVersions("CHANGED"),
        )
        assert builder.create_cropped_file_text("a.svg", "text", "Someone") == "CHANGED|Someone"


class TestOriginalFileTextUpdater:
    """Tests for ``OriginalFileTextUpdater``."""

    def test_appends_to_existing_template(self):
        result = OriginalFileTextUpdater().append_image_extracted_template("File:b.svg", "{{Image extracted|a.svg}}")
        assert result == "{{Image extracted|a.svg|2=b.svg}}"

    def test_append_returns_text_without_template(self):
        assert OriginalFileTextUpdater().append_image_extracted_template("b.svg", "plain") == "plain"

    def test_update_returns_text_when_file_already_mentioned(self):
        assert OriginalFileTextUpdater().update_original_file_text("b.svg", "has b.svg") == "has b.svg"

    def test_update_prefers_existing_template(self):
        result = OriginalFileTextUpdater().update_original_file_text("File:b_c.svg", "{{Image extracted|a.svg}}")
        assert result == "{{Image extracted|a.svg|2=b c.svg}}"

    def test_update_falls_back_to_other_versions_then_inserter(self):
        other_versions = FakeOtherVersions()
        inserter = FakeInserter()
        updater = OriginalFileTextUpdater(inserter=inserter, other_versions=other_versions)
        assert updater.update_original_file_text("b.svg", "plain") == "INSERTED"
        assert other_versions.calls == [("Image extracted", "b.svg")]
        assert inserter.calls == [("plain", "{{Image extracted|1=b.svg}}")]


class TestInformationAuthorUpdater:
    """Tests for ``InformationAuthorUpdater.update_information_author``."""

    def test_empty_citation_leaves_text_unchanged(self):
        assert InformationAuthorUpdater().update_information_author("text", "") == "text"

    @needs_wtp
    def test_replaces_our_world_in_data(self):
        text = "{{Information\n|author=Our World in Data\n}}"
        result = InformationAuthorUpdater().update_information_author(text, "Cited")
        assert "Cited" in result
        assert "Our World" not in result

    @needs_wtp
    def test_text_without_information_template_is_unchanged(self):
        assert InformationAuthorUpdater().update_information_author("plain", "Cited") == "plain"
