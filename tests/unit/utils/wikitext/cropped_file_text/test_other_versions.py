"""Tests for the wikitext.cropped_file_text.other_versions module."""

from __future__ import annotations

import wikitextparser as wtp

from src.main_app.utils.wikitext.cropped_file_text import add_other_versions_new
from src.main_app.utils.wikitext.cropped_file_text.other_versions import (
    OtherVersionsAdder,
)


class TestGetArgs:
    """Tests for the _get_argument function."""

    def test_basic(self) -> None:
        text_raw = """{{Information |description={{en|1=Daily per capita supply of all meat, World}} |author = Our World In Data |date= 2022 |Other_versions={{Extracted from|1=Daily meat consumption per person, World, 2022.svg}}}}"""
        template = wtp.Template(text_raw)
        args_in = OtherVersionsAdder._get_argument(template, ["other versions", "other_versions"])
        assert args_in is not None
        assert args_in.value == "{{Extracted from|1=Daily meat consumption per person, World, 2022.svg}}"
        assert args_in.name == "Other_versions"

    def test_basic_args(self) -> None:
        text_raw = """{{Extracted from| 1 =  Daily meat consumption per person, World, 2022.svg}}"""
        template = wtp.Template(text_raw)
        args_in = OtherVersionsAdder._get_argument(template, ["1"])
        assert args_in is not None
        assert args_in.value == "  Daily meat consumption per person, World, 2022.svg"
        assert args_in.name == " 1 "

    def test_basic_args_not_named(self) -> None:
        text_raw = """ hello? {{Extracted from | Daily meat consumption per person, World, 2022.svg}} zz"""
        template = wtp.WikiText(text_raw).templates[0]
        assert template.name.strip() == "Extracted from"
        args_in = OtherVersionsAdder._get_argument(template, ["1"])
        assert args_in is not None
        assert args_in.value.strip() == "Daily meat consumption per person, World, 2022.svg"
        assert args_in.name == "1"

    def test_with_add_other_versions_new(self) -> None:
        """Test that template is added to existing content."""
        text = "{{Information|description=A cropped image|other_versions={{Extracted from| 1=Original test.svg |z=}}}}"

        # text_to_add = "{{Extracted from|1=Original.svg}}"

        result = add_other_versions_new(
            text=text,
            temp_name="Extracted from",
            first_param_valve="original_test.svg",
            main_template_name="Information",
            main_template_args=["other versions", "other_versions"],
        )

        # The other versions parameter is added to the Information template
        assert "|other versions=" not in result

        assert result == text, "text should be equal to text"

        assert result.count("{{Extracted from|") == 1


class TestAddOtherVersionsNew:
    """Tests for the add_other_versions_new function."""

    def test_basic(self) -> None:
        text_input = """{{Information |description={{en|1=Daily per capita supply of all meat, World}} |author = Our World In Data |date= 2022 }}"""

        text_output = """{{Information |description={{en|1=Daily per capita supply of all meat, World}} |author = Our World In Data |date= 2022 |other versions={{Extracted from|1=Daily meat consumption per person, World, 2022.svg}}}}"""
        result = add_other_versions_new(
            text=text_input,
            temp_name="Extracted from",
            first_param_valve="Daily meat consumption per person, World, 2022.svg",
            main_template_name="Information",
            main_template_args=["other versions", "other_versions"],
        )
        assert result == text_output

    def test_basic_no_changes(self) -> None:
        text_input = """{{Information |description={{en|1=Daily per capita supply of all meat, World}} |author = Our World In Data |date= 2022 |Other_versions={{Extracted from|1=Daily meat consumption per person, World, 2022.svg}}}}"""

        result = add_other_versions_new(
            text=text_input,
            temp_name="Extracted from",
            first_param_valve="Daily meat consumption per person, World, 2022.svg",
            main_template_name="Information",
            main_template_args=["other versions", "other_versions"],
        )
        assert result == text_input

    def test_basic_not_duplicate(self) -> None:
        text_input = """{{Information |description={{en|1=Daily per capita supply of all meat, World}} |author = Our World In Data |date= 2022 |Other_versions={{Extracted from|Daily meat consumption per person, World, 2022.svg}}}}"""

        text_output = """{{Information |description={{en|1=Daily per capita supply of all meat, World}} |author = Our World In Data |date= 2022 |Other_versions={{Extracted from|1=Daily meat consumption per person, World, 2022.svg}}}}"""

        result = add_other_versions_new(
            text=text_input,
            temp_name="Extracted from",
            first_param_valve="Daily meat consumption per person, World, 2022.svg",
            main_template_name="Information",
            main_template_args=["other versions", "other_versions"],
        )
        assert result == text_input


class TestAddOtherVersions:
    """Tests for the add_other_versions_new function."""

    def test_add_other_versions_to_information_template(self):
        """Test adding other versions parameter to an Information template."""
        text_input = """{{Information\n|description={{en|1=Daily per capita supply of all meat, World}}\n|author = Our World In Data\n|date= 2022\n|source = https://ourworldindata.org/grapher/daily-meat-consumption-per-person\n|permission = "License: All of Our World in Data is completely open access and all work is licensed under the Creative Commons BY license. You have the permission to use, distribute, and reproduce in any medium, provided the source and authors are credited."\n}}"""

        result = add_other_versions_new(
            text=text_input,
            temp_name="Extracted from",
            first_param_valve="Daily meat consumption per person, World, 2022.svg",
            main_template_name="Information",
            main_template_args=["other versions", "other_versions"],
        )

        assert "|other versions={{Extracted from|1=Daily meat consumption per person, World, 2022.svg}}" in result
        # Verify other parameters are preserved
        assert "|description={{en|1=Daily per capita supply of all meat, World}}" in result
        assert "|author = Our World In Data" in result
        assert "|date= 2022" in result

    def test_add_other_versions_with_extracted_from_template(self):
        """Test adding other versions with an Extracted from template value."""
        text_input = """{{Information\n|description={{en|1=Some description}}\n|author = Test Author\n}}"""

        extracted_text = "{{Extracted from|1=Daily meat consumption per person, World, 2022.svg}}"
        result = add_other_versions_new(
            text=text_input,
            temp_name="Extracted from",
            first_param_valve="Daily meat consumption per person, World, 2022.svg",
            main_template_name="Information",
            main_template_args=["other versions", "other_versions"],
        )

        assert f"|other versions={extracted_text}" in result

    def test_no_information_template_returns_original(self):
        """Test that text without Information template is returned unchanged."""
        text_input = """{{SomeOtherTemplate\n|param1=value1\n}}"""

        result = add_other_versions_new(
            text=text_input,
            temp_name="Extracted from",
            first_param_valve="Daily meat consumption per person, World, 2022.svg",
            main_template_name="Information",
            main_template_args=["other versions", "other_versions"],
        )

        assert result == text_input
