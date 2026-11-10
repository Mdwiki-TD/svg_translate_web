from src.main_app.utils.new_wikitext.file_references import FileReferenceUpdater


class TestUpdateTemplatePageFileReference:
    """Tests for the FileReferenceUpdater.update_template_page_file_reference function."""

    def test_replaces_file_reference_in_template(self):
        """Test replacing file reference in a template page."""
        text = """|file         = [[File:barley yields, World, 2023.svg|link=|thumb|upright=1.6|Barley yields]]"""
        result = FileReferenceUpdater.update_template_page_file_reference(
            "File:barley yields, World, 2023.svg",
            "File:barley yields, World, 2023 (cropped).svg",
            text,
        )
        assert "[[File:barley yields, World, 2023 (cropped).svg|" in result
        assert "[[File:barley yields, World, 2023.svg|" not in result

    def test_replaces_all_occurrences_including_syntaxhighlight(self):
        """Test that all occurrences are replaced, including in syntaxhighlight blocks."""
        text = (
            "{{owidslider\n"
            "|file         = [[File:barley yields, World, 2023.svg|link=|thumb|upright=1.6|Barley yields]]\n"
            "}}\n"
            '<syntaxhighlight lang="wikitext">\n'
            "{{owidslider\n"
            "|file         = [[File:barley yields, World, 2023.svg|link=|thumb|upright=1.6|Barley yields]]\n"
            "}}\n"
            "</syntaxhighlight>"
        )
        result = FileReferenceUpdater.update_template_page_file_reference(
            "File:barley yields, World, 2023.svg",
            "File:barley yields, World, 2023 (cropped).svg",
            text,
        )
        assert result.count("[[File:barley yields, World, 2023 (cropped).svg|") == 2
        assert "[[File:barley yields, World, 2023.svg|" not in result

    def test_handles_filename_without_file_prefix(self):
        """Test that filenames without File: prefix are handled correctly."""
        text = "|file = [[File:barley yields, World, 2023.svg|link=]]"
        result = FileReferenceUpdater.update_template_page_file_reference(
            "barley yields, World, 2023.svg",
            "barley yields, World, 2023 (cropped).svg",
            text,
        )
        assert "[[File:barley yields, World, 2023 (cropped).svg|" in result
        assert "[[File:barley yields, World, 2023.svg|" not in result

    def test_returns_unchanged_text_when_no_match(self):
        """Test that text is returned unchanged when original file is not found."""
        text = "|file = [[File:other file.svg|link=]]"
        result = FileReferenceUpdater.update_template_page_file_reference(
            "File:barley yields, World, 2023.svg",
            "File:barley yields, World, 2023 (cropped).svg",
            text,
        )
        assert result == text

    def test_returns_unchanged_empty_text(self):
        """Test that empty text is returned unchanged."""
        result = FileReferenceUpdater.update_template_page_file_reference(
            "File:barley yields, World, 2023.svg",
            "File:barley yields, World, 2023 (cropped).svg",
            "",
        )
        assert result == ""

    def test_replace_file_reference_basic(self) -> None:
        """Test replacing a file reference in template page."""
        text = "[[File:Original.svg|link=|thumb|Description]]"
        result = FileReferenceUpdater.update_template_page_file_reference("Original.svg", "Cropped.svg", text)
        assert result == "[[File:Cropped.svg|link=|thumb|Description]]"

    def test_replace_file_reference_with_file_prefix(self) -> None:
        """Test replacing file reference when names include 'File:' prefix."""
        text = "[[File:Original.svg|link=|thumb]]"
        result = FileReferenceUpdater.update_template_page_file_reference("File:Original.svg", "File:Cropped.svg", text)
        assert result == "[[File:Cropped.svg|link=|thumb]]"

    def test_replace_multiple_file_references(self) -> None:
        """Test replacing multiple file references."""
        text = "[[File:Original.svg|thumb]][[File:Original.svg|link=]]"
        result = FileReferenceUpdater.update_template_page_file_reference("Original.svg", "Cropped.svg", text)
        assert result == "[[File:Cropped.svg|thumb]][[File:Cropped.svg|link=]]"

    def test_replace_in_syntaxhighlight_block(self) -> None:
        """Test replacing file reference inside syntaxhighlight block."""
        text = '<syntaxhighlight lang="wikitext">[[File:Original.svg|thumb]]</syntaxhighlight>'
        result = FileReferenceUpdater.update_template_page_file_reference("Original.svg", "Cropped.svg", text)
        assert "[[File:Cropped.svg|thumb]]" in result

    def test_no_file_reference(self) -> None:
        """Test text without file reference returns unchanged."""
        text = "Some text without file references"
        result = FileReferenceUpdater.update_template_page_file_reference("Original.svg", "Cropped.svg", text)
        assert result == text

    def test_empty_text(self) -> None:
        """Test empty text returns empty."""
        result = FileReferenceUpdater.update_template_page_file_reference("Original.svg", "Cropped.svg", "")
        assert result == ""

    def test_partial_match_not_replaced(self) -> None:
        """Test that partial matches are not replaced."""
        text = "[[File:OriginalOld.svg|thumb]]"
        result = FileReferenceUpdater.update_template_page_file_reference("Original.svg", "Cropped.svg", text)
        assert result == text  # Should not change

    def test_different_file_not_replaced(self) -> None:
        """Test that different file references are not replaced."""
        text = "[[File:OtherFile.svg|thumb]]"
        result = FileReferenceUpdater.update_template_page_file_reference("Original.svg", "Cropped.svg", text)
        assert result == text

    def test_mixed_case_file_names(self) -> None:
        """Test that replacement is case-sensitive."""
        text = "[[File:original.svg|thumb]]"
        result = FileReferenceUpdater.update_template_page_file_reference("Original.svg", "Cropped.svg", text)
        # Case-sensitive, so no replacement
        assert result == text

    def test_file_reference_with_multiple_parameters(self) -> None:
        """Test replacing file reference with multiple parameters."""
        text = "[[File:Original.svg|link=|thumb|upright=1.6|Description text]]"
        result = FileReferenceUpdater.update_template_page_file_reference("Original.svg", "Cropped.svg", text)
        assert result == "[[File:Cropped.svg|link=|thumb|upright=1.6|Description text]]"


class TestFileReferenceUpdaterTemplatePage:
    """Tests for ``FileReferenceUpdater.update_template_page_file_reference``."""

    def test_replaces_all_references(self):
        text = "[[File:a.svg|thumb]] and [[File:a.svg|x]]"
        result = FileReferenceUpdater.update_template_page_file_reference("File:a.svg", "b.svg", text)
        assert result == "[[File:b.svg|thumb]] and [[File:b.svg|x]]"

    def test_ignores_other_files(self):
        text = "[[File:az.svg|thumb]]"
        assert FileReferenceUpdater.update_template_page_file_reference("a.svg", "b.svg", text) == text


class TestFileReferenceUpdaterEnsurePrefix:
    """Tests for ``FileReferenceUpdater.ensure_prefix``."""

    def test_adds_prefix(self):
        assert FileReferenceUpdater.ensure_prefix("a.svg") == "File:a.svg"

    def test_keeps_existing_prefix(self):
        assert FileReferenceUpdater.ensure_prefix("File:a.svg") == "File:a.svg"

    def test_returns_empty_and_non_string_as_is(self):
        assert FileReferenceUpdater.ensure_prefix("") == ""
        assert FileReferenceUpdater.ensure_prefix(None) is None

    def test_adds_prefix_when_missing(self):
        """Test that File: prefix is added when missing."""
        result = FileReferenceUpdater.ensure_prefix("Example.svg")
        assert result == "File:Example.svg"

    def test_does_not_add_prefix_when_present(self):
        """Test that File: prefix is not added when already present."""
        result = FileReferenceUpdater.ensure_prefix("File:Example.svg")
        assert result == "File:Example.svg"

    def test_handles_empty_string(self):
        """Test handling of empty string."""
        result = FileReferenceUpdater.ensure_prefix("")
        assert result == ""

    def test_handles_prefix_with_different_case(self):
        """Test that only exact 'File:' prefix is recognized."""
        # "file:" (lowercase) should get prefix added
        result = FileReferenceUpdater.ensure_prefix("file:Example.svg")
        assert result == "File:file:Example.svg"

    def test_handles_prefix_in_middle(self):
        """Test that File: in the middle doesn't count as prefix."""
        result = FileReferenceUpdater.ensure_prefix("Example_File:test.svg")
        assert result == "File:Example_File:test.svg"
