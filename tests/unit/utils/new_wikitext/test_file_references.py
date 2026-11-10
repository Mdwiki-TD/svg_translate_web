from src.main_app.utils.new_wikitext.file_references import FileReferenceUpdater


class TestFileReferenceUpdaterEnsurePrefix:
    """Tests for ``FileReferenceUpdater.ensure_prefix``."""

    def test_adds_prefix(self):
        assert FileReferenceUpdater().ensure_prefix("a.svg") == "File:a.svg"

    def test_keeps_existing_prefix(self):
        assert FileReferenceUpdater().ensure_prefix("File:a.svg") == "File:a.svg"

    def test_returns_empty_and_non_string_as_is(self):
        updater = FileReferenceUpdater()
        assert updater.ensure_prefix("") == ""
        assert updater.ensure_prefix(None) is None


class TestFileReferenceUpdaterTemplatePage:
    """Tests for ``FileReferenceUpdater.update_template_page_file_reference``."""

    def test_replaces_all_references(self):
        text = "[[File:a.svg|thumb]] and [[File:a.svg|x]]"
        result = FileReferenceUpdater().update_template_page_file_reference("File:a.svg", "b.svg", text)
        assert result == "[[File:b.svg|thumb]] and [[File:b.svg|x]]"

    def test_ignores_other_files(self):
        text = "[[File:az.svg|thumb]]"
        assert FileReferenceUpdater().update_template_page_file_reference("a.svg", "b.svg", text) == text
