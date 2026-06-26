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
        assert find_newest_year(TEMPLATE_EXAMPLE) == 2025
