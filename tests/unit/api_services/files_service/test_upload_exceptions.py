from __future__ import annotations

from src.main_app.api_services.files_service.exceptions import SharedFileExistsError


class TestSharedFileExistsError:
    def test_existing_file_name(self):
        error = SharedFileExistsError(
            "A file with this name already exists in the shared file repository. If you still want to upload your file, please go back and use a new name. [[File:Share_of_deaths_obesity,_AFG.svg|thumb|center|Share_of_deaths_obesity,_AFG.svg]]",
        )
        assert error.existing_file_name == "File:Share_of_deaths_obesity,_AFG.svg"


# ── SharedFileExistsError – additional coverage ────────────────────────────


# Reusable info strings
_INFO_FILE_PREFIX = (
    "A file with this name already exists in the shared file repository. "
    "If you still want to upload your file, please go back and use a new name. "
    "[[File:Example.svg|thumb|center|Example.svg]]"
)

_INFO_IMAGE_PREFIX = (
    "A file with this name already exists in the shared file repository. [[Image:Old_name.png|thumb|Old_name.png]]"
)

_INFO_NO_WIKILINK = (
    "A file with this name already exists in the shared file repository. "
    "If you still want to upload your file, please go back and use a new name."
)


class TestSharedFileExistsErrorAttributes:
    def test_code_attribute(self) -> None:
        error = SharedFileExistsError(_INFO_FILE_PREFIX)
        assert error.code == "fileexists-shared-forbidden"

    def test_info_attribute_preserved(self) -> None:
        error = SharedFileExistsError(_INFO_FILE_PREFIX)
        assert error.info == _INFO_FILE_PREFIX

    def test_is_exception_subclass(self) -> None:
        error = SharedFileExistsError(_INFO_FILE_PREFIX)
        assert isinstance(error, Exception)

    def test_str_contains_info(self) -> None:
        error = SharedFileExistsError(_INFO_FILE_PREFIX)
        assert "Example.svg" in str(error)


class TestSharedFileExistsErrorExtractFileName:
    """Tests for the static _extract_file_name helper."""

    def test_file_prefix(self) -> None:
        assert SharedFileExistsError._extract_file_name(_INFO_FILE_PREFIX) == "File:Example.svg"

    def test_image_prefix(self) -> None:
        assert SharedFileExistsError._extract_file_name(_INFO_IMAGE_PREFIX) == "Image:Old_name.png"

    def test_no_wikilink_returns_none(self) -> None:
        assert SharedFileExistsError._extract_file_name(_INFO_NO_WIKILINK) is None

    def test_empty_string_returns_none(self) -> None:
        assert SharedFileExistsError._extract_file_name("") is None

    def test_pipe_in_name_strips_extra_params(self) -> None:
        info = "Some text [[File:MyFile.svg|200px]]"
        assert SharedFileExistsError._extract_file_name(info) == "File:MyFile.svg"

    def test_whitespace_around_name(self) -> None:
        info = "text [[File:  Spaced.svg  |thumb]]"
        assert SharedFileExistsError._extract_file_name(info) == "File:Spaced.svg"

    def test_only_pipe_after_name(self) -> None:
        """Wikilink with only a pipe and no additional params: [[File:Name.svg|]]"""
        info = "text [[File:Bare.svg|]]"
        assert SharedFileExistsError._extract_file_name(info) == "File:Bare.svg"

    def test_multiple_wikilinks_uses_first(self) -> None:
        info = "text [[File:First.svg|thumb]] more [[File:Second.svg|thumb]]"
        assert SharedFileExistsError._extract_file_name(info) == "File:First.svg"

    def test_existing_file_name_set_via_init(self) -> None:
        error = SharedFileExistsError(_INFO_IMAGE_PREFIX)
        assert error.existing_file_name == "Image:Old_name.png"

    def test_existing_file_name_none_when_no_link(self) -> None:
        error = SharedFileExistsError(_INFO_NO_WIKILINK)
        assert error.existing_file_name is None

    def test_existing_file_name_none_when_empty(self) -> None:
        error = SharedFileExistsError("")
        assert error.existing_file_name is None


class TestSharedFileExistsErrorExtractFileNameEdgeCases:
    """Edge-case paths for _extract_file_name."""

    def test_lowercase_file_prefix(self) -> None:
        """The regex is case-sensitive — lowercase 'file:' should not match."""
        info = "text [[file:lowercase.svg|thumb]]"
        assert SharedFileExistsError._extract_file_name(info) is None

    def test_mixed_case_image_prefix(self) -> None:
        """Case-sensitive regex — 'IMAGE:' should not match."""
        info = "text [[IMAGE:Upper.png|thumb]]"
        assert SharedFileExistsError._extract_file_name(info) is None

    def test_spaces_around_colon(self) -> None:
        """Wikilink with spaces between prefix and colon: [[File : Name.svg|...]]"""
        info = "text [[File : Spaced.svg|thumb]]"
        # regex allows \s* around the colon
        result = SharedFileExistsError._extract_file_name(info)
        assert result is not None
        assert "Spaced.svg" in result

    def test_filename_with_special_chars(self) -> None:
        info = "text [[File:Death_rate_(obesity),_AFG.svg|thumb|caption]]"
        assert SharedFileExistsError._extract_file_name(info) == "File:Death_rate_(obesity),_AFG.svg"

    def test_empty_wikilink_brackets(self) -> None:
        """Empty brackets [[ ]] should not match."""
        info = "text [[  ]]"
        assert SharedFileExistsError._extract_file_name(info) is None

    def test_extract_file_name_is_static(self) -> None:
        """Confirm _extract_file_name can be called on the class directly."""
        assert SharedFileExistsError._extract_file_name("[[File:X.svg|]]") == "File:X.svg"
