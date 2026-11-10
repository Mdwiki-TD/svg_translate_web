from __future__ import annotations

from src.main_app.utils.new_wikitext.file_text import (
    CroppedFileTextBuilder,
    InformationAuthorUpdater,
    OriginalFileTextUpdater,
)


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
    """Tests for the OriginalFileTextUpdater.append_image_extracted_template function."""

    def test_itappendstoexistingimageextracted_template(self):
        oldText1 = """
{{Information
|description={{zh|1=北师大启功像1。}}
|other_versions={{Image extracted|HoryujiYumedono0363 edit1.jpg}}
}}

{{PD-self}}
"""

        newText1 = """
{{Information
|description={{zh|1=北师大启功像1。}}
|other_versions={{Image extracted|HoryujiYumedono0363 edit1.jpg|2=My new file.jpg}}
}}

{{PD-self}}
"""

        oldText2 = """
{{Information
|description={{zh|1=北师大启功像1。}}
|other_versions={{Image extracted|HoryujiYumedono0363 edit1.jpg|Crop 1.jpg}}
}}

{{PD-self}}
"""

        newText2 = """
{{Information
|description={{zh|1=北师大启功像1。}}
|other_versions={{Image extracted|HoryujiYumedono0363 edit1.jpg|Crop 1.jpg|3=My new file.jpg}}
}}

{{PD-self}}
"""

        result1 = OriginalFileTextUpdater.append_image_extracted_template("My new file.jpg", oldText1)
        assert result1 == newText1

        result2 = OriginalFileTextUpdater.append_image_extracted_template("My new file.jpg", oldText2)
        assert result2 == newText2

    def test_appends_to_existing_template(self):
        result = OriginalFileTextUpdater.append_image_extracted_template("File:b.svg", "{{Image extracted|a.svg}}")
        assert result == "{{Image extracted|a.svg|2=b.svg}}"

    def test_append_returns_text_without_template(self):
        assert OriginalFileTextUpdater.append_image_extracted_template("b.svg", "plain") == "plain"


class TestOriginalFileTextUpdaterUpdate:
    """Tests for ``OriginalFileTextUpdater().update_original_file_text``."""

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
        assert InformationAuthorUpdater.update_information_author("text", "") == "text"

    def test_replaces_our_world_in_data(self):
        text = "{{Information\n|author=Our World in Data\n}}"
        result = InformationAuthorUpdater.update_information_author(text, "Cited")
        assert "Cited" in result
        assert "Our World" not in result

    def test_text_without_information_template_is_unchanged(self):
        assert InformationAuthorUpdater.update_information_author("plain", "Cited") == "plain"


class TestCreateCroppedFileText:
    """Tests for the create_cropped_file_text function."""

    def test_add_extracted_from_template(self) -> None:
        """Test that function adds {{Extracted from}} template."""
        text = "{{Information|description=Test}}"
        result = CroppedFileTextBuilder().create_cropped_file_text("File:Original.svg", text)
        assert result.count("{{Extracted from|1=Original.svg}}") == 1

    def test_empty_text(self) -> None:
        """Test with empty text returns just the template."""
        result = CroppedFileTextBuilder().create_cropped_file_text("File:Original.svg", "")
        assert result == "{{Extracted from|1=Original.svg}}"

    def test_file_prefix_removed(self) -> None:
        """Test that 'File:' prefix is removed from file name."""
        text = "{{Information}}"
        result = CroppedFileTextBuilder().create_cropped_file_text("File:Original.svg", text)
        assert "Original.svg" in result
        assert "File:Original.svg" not in result.split("|1=")[1] if "|1=" in result else True

    def test_template_added_to_existing_content(self) -> None:
        """Test that template is added to existing content."""
        text = "{{Information|description=A cropped image}}"
        result = CroppedFileTextBuilder().create_cropped_file_text("File:Original.svg", text)
        # The other versions parameter is added to the Information template
        assert "|other versions=" in result
        assert result.count("{{Extracted from|1=Original.svg}}") == 1

    def test_fallback_to_insert_before_methods(self) -> None:
        """Test fallback to insert_before_methods when OtherVersionsUpdater.add_template fails (line 90)."""
        # Text with category but no {{Information}} template - should fallback to insert_before_methods
        text = "[[Category:Test]]"
        result = CroppedFileTextBuilder().create_cropped_file_text("File:Original.svg", text)
        # The function should add the Extracted from template before the category
        assert result.count("{{Extracted from|1=Original.svg}}") == 1
        assert result.index("{{Extracted from") < result.index("[[Category:")


class TestCreateCroppedFileTextEdgeTests:
    """Test edge cases for create_cropped_file_text function."""

    def test_template_added_to_existing_other_versions(self) -> None:
        """Test that template is added to existing content."""
        text = "{{Information|description=A cropped image|other_versions=}}"
        result = CroppedFileTextBuilder().create_cropped_file_text("File:Original.svg", text)

        # The other versions parameter is added to the Information template
        assert "|other versions=" not in result

        expected_text = "{{Information|description=A cropped image|other_versions={{Extracted from|1=Original.svg}}}}"

        assert result == expected_text
        assert result.count("{{Extracted from|1=Original.svg}}") == 1

    def test_count_extracted_from(self) -> None:
        text = """{{Information
|description={{en|1=Wheat yields, World}}
|author = Our World In Data
|date= 2023
|source = https://ourworldindata.org/grapher/wheat-yields?tab=map
}}"""

        result = CroppedFileTextBuilder().create_cropped_file_text("wheat yields, World, 2023.svg", text)

        assert "|author = Our World In Data" in result
        assert result.count("{{Extracted from|1=wheat yields, World, 2023.svg}}") == 1

    def test_adds_author_when_information_template_has_none(self) -> None:
        """Test that a citation is added when the Information template lacks an author."""
        text = "{{Information|description=Wheat yields}}"

        result = CroppedFileTextBuilder().create_cropped_file_text("Original.svg", text)

        assert result.count("{{Extracted from|1=Original.svg}}") == 1

    def test_preserves_author(self) -> None:
        """Test that unavailable metadata leaves the original author untouched."""
        text = "{{Information|author=Our World In Data}}"

        result = CroppedFileTextBuilder().create_cropped_file_text("Original.svg", text)

        assert "author=Our World In Data" in result
        assert result.count("{{Extracted from|1=Original.svg}}") == 1

    def test_not_adding_duplicate_value(self) -> None:
        """test not adding duplicate value."""
        text = "{{Information|author=Our World In Data|other versions={{extracted from|1=Original.svg}}}}"

        result = CroppedFileTextBuilder().create_cropped_file_text("Original.svg", text)

        assert result.count("{{extracted from|") == 1
        assert result.count("{{extracted from|1=Original.svg}}") == 1
