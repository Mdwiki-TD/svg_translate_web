"""Tests for the owidslidersrcs_utils.find_newest_year module."""

from __future__ import annotations

from src.main_app.utils.wikitext.owid_sliders_rcs.owidslidersrcs_utils import (
    find_newest_year,
)

TEMPLATE_EXAMPLE = """
{{ owidslidersrcs |id=gallery|widths=240|heights=240
|gallery-Africa=
File:Deforestation embedded trade, Africa, 2017.svg!year=2017
File:Deforestation embedded trade, Africa, 2018.svg!year=2018
File:Deforestation embedded trade, Africa, 2019.svg!year=2019
File:Deforestation embedded trade, Africa, 2020.svg!year=2020
File:Deforestation embedded trade, Africa, 2021.svg!year=2021
|gallery-World=
File:Deforestation embedded trade, World, 2015.svg!year=2015
File:Deforestation embedded trade, World, 2016.svg!year=2016
File:Deforestation embedded trade, World, 2017.svg!year=2017
File:Deforestation embedded trade, World, 2018.svg!year=2018
|gallery-NorthAmerica=
File:Deforestation embedded trade, North America, 2018.svg!year=2018
|gallery-Oceania=
File:Deforestation embedded trade, Oceania, 2022.svg!year=2022
File:Deforestation embedded trade, Oceania, 2023.svg!year=2023
|gallery-Europe=
File:Deforestation embedded trade, Europe, 2023.svg!year = 2023
|gallery-Asia=x
File:Deforestation embedded trade, Asia, 2021.svg!year=2021
File:Deforestation embedded trade, Asia, 2022.svg!year=2022
File:Deforestation embedded trade, Asia, 2023.svg!year=2023
|gallery-SouthAmerica=
File:Deforestation embedded trade, South America, 2021.svg!year=2021
File:Deforestation embedded trade, South America, 2022.svg!year=2022
File:Deforestation embedded trade, South America, 2023.svg!year=2023
File:Deforestation embedded trade, South America, 2025.svg! year  = 2025
|gallery-AllCountries=
}}"""


class TestFindNewestYear:
    """Tests for find_newest_year function."""

    def test_basic(self):
        """Test happy path with multiple galleries and years."""
        assert find_newest_year(TEMPLATE_EXAMPLE) == 2025

    def test_empty_text_returns_none(self):
        """Test that empty text returns None."""
        assert find_newest_year("") is None

    def test_no_template_returns_none(self):
        """Test that text without owidslidersrcs template returns None."""
        text = "Some random text without the template."
        assert find_newest_year(text) is None

    def test_template_no_year_entries_returns_none(self):
        """Test that template without any !year= entries returns None."""
        text = """
        {{owidslidersrcs|id=gallery|widths=240
        |gallery-World=
        File:test.svg
        File:other.svg
        }}
        """
        assert find_newest_year(text) is None

    def test_single_year_entry(self):
        """Test with a single year entry returns that year."""
        text = """
        {{owidslidersrcs|gallery-World=
        File:test.svg!year=2020
        }}
        """
        assert find_newest_year(text) == 2020

    def test_multiple_years_returns_max(self):
        """Test that multiple years returns the maximum."""
        text = """
        {{owidslidersrcs|gallery-World=
        File:a.svg!year=2010
        File:b.svg!year=2015
        File:c.svg!year=2020
        }}
        """
        assert find_newest_year(text) == 2020

    def test_years_not_in_order(self):
        """Test that years are correctly identified when not sorted."""
        text = """
        {{owidslidersrcs|gallery-World=
        File:a.svg!year=2020
        File:b.svg!year=2010
        File:c.svg!year=2015
        }}
        """
        assert find_newest_year(text) == 2020

    def test_case_insensitive_template_name_uppercase(self):
        """Test case-insensitive matching with uppercase template name."""
        text = """
        {{OWIDSLIDERSRCS|gallery-World=
        File:test.svg!year=2023
        }}
        """
        assert find_newest_year(text) == 2023

    def test_case_insensitive_template_name_mixed(self):
        """Test case-insensitive matching with mixed-case template name."""
        text = """
        {{OwidSliderSrcs|gallery-World=
        File:test.svg!year=2022
        }}
        """
        assert find_newest_year(text) == 2022

    def test_whitespace_around_year_equals(self):
        """Test various whitespace patterns around !year=."""
        text = """
        {{owidslidersrcs|gallery-World=
        File:a.svg!year=2020
        File:b.svg! year = 2021
        File:c.svg!  year  =  2022
        }}
        """
        assert find_newest_year(text) == 2022

    def test_duplicate_years(self):
        """Test duplicate years don't cause issues."""
        text = """
        {{owidslidersrcs|gallery-World=
        File:a.svg!year=2020
        File:b.svg!year=2020
        File:c.svg!year=2020
        }}
        """
        assert find_newest_year(text) == 2020

    def test_all_same_year(self):
        """Test that same year across galleries returns correctly."""
        text = """
        {{owidslidersrcs|gallery-World=
        File:a.svg!year=2022
        |gallery-Europe=
        File:b.svg!year=2022
        |gallery-Asia=
        File:c.svg!year=2022
        }}
        """
        assert find_newest_year(text) == 2022

    def test_multiple_templates_only_first_processed(self):
        """Test that only the first owidslidersrcs template is processed."""
        text = """
        {{owidslidersrcs|gallery-World=
        File:a.svg!year=2010
        }}
        {{owidslidersrcs|gallery-World=
        File:b.svg!year=2020
        }}
        """
        # First template has max 2010, second has 2020, but function only
        # processes the first template.
        assert find_newest_year(text) == 2010

    def test_first_template_no_years_second_ignored(self):
        """Test that if first template has no year entries, second is still ignored."""
        text = """
        {{owidslidersrcs|gallery-World=
        File:a.svg
        }}
        {{owidslidersrcs|gallery-World=
        File:b.svg!year=2020
        }}
        """
        assert find_newest_year(text) is None

    def test_year_with_extra_whitespace_in_template(self):
        """Test whitespace between ! and year and around = is handled."""
        text = """
        {{ owidslidersrcs | gallery-World =
        File:test.svg!year=2023
        }}
        """
        assert find_newest_year(text) == 2023

    def test_template_with_no_gallery_world_still_matches(self):
        """Test that find_newest_year works on the whole template, not just gallery-World."""
        text = """
        {{owidslidersrcs
        |gallery-Other=
        File:test.svg!year=2024
        }}
        """
        # The function regex-matches the entire template text, not just a specific gallery.
        assert find_newest_year(text) == 2024
