"""Tests for the wikitext.other_versions module."""

from __future__ import annotations

from src.main_app.utils.wikitext.other_versions import add_other_versions


class TestAddOtherVersions:
    """Tests for the add_other_versions function."""

    def test_add_other_versions_to_information_template(self):
        """Test adding other versions parameter to an Information template."""
        text_input = """{{Information
|description={{en|1=Daily per capita supply of all meat, World}}
|author = Our World In Data
|date= 2022
|source = https://ourworldindata.org/grapher/daily-meat-consumption-per-person
|permission = "License: All of Our World in Data is completely open access and all work is licensed under the Creative Commons BY license. You have the permission to use, distribute, and reproduce in any medium, provided the source and authors are credited."
}}"""

        result = add_other_versions("{{Extracted from|1=Daily meat consumption per person, World, 2022.svg}}", text_input)

        assert "|other versions={{Extracted from|1=Daily meat consumption per person, World, 2022.svg}}" in result
        # Verify other parameters are preserved
        assert "|description={{en|1=Daily per capita supply of all meat, World}}" in result
        assert "|author = Our World In Data" in result
        assert "|date= 2022" in result

    def test_add_other_versions_with_extracted_from_template(self):
        """Test adding other versions with an Extracted from template value."""
        text_input = """{{Information
|description={{en|1=Some description}}
|author = Test Author
}}"""

        extracted_text = "{{Extracted from|1=Daily meat consumption per person, World, 2022.svg}}"
        result = add_other_versions(extracted_text, text_input)

        assert f"|other versions={extracted_text}" in result

    def test_no_information_template_returns_original(self):
        """Test that text without Information template is returned unchanged."""
        text_input = """{{SomeOtherTemplate
|param1=value1
}}"""

        result = add_other_versions("{{Extracted from|1=Daily meat consumption per person, World, 2022.svg}}", text_input)

        assert result == text_input

    def test_add_other_versions_preserves_template_structure(self):
        """Test that the template structure is preserved after adding other versions."""
        text_input = """{{Information
|description=Test
|author=Author
|other_versions=
}}"""

        result = add_other_versions("Other version info", text_input)

        # Check that the result starts and ends with the template brackets
        assert result.startswith("{{Information")
        assert result.endswith("}}")
        # Check that other versions is in the template
        assert "|other_versions=Other version info" in result
