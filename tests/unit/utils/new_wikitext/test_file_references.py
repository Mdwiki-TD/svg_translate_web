from src.main_app.utils.new_wikitext.file_references import FileReferenceUpdater


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
