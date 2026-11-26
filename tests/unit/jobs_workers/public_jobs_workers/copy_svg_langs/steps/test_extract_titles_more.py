from __future__ import annotations

from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps import ExtractSteps

WIKITEXT = """*[[Commons:List of interactive graphs|Return to list]]

{{owidslider
|start        = 2024
|list         = Template:OWID/Absolute change co2#gallery
|location      = commons
|caption      =
|title        =
|language     =
|file         = [[File:absolute change co2, World, 2024 (cropped).svg|link=|thumb|upright=1.6|Absolute change co2]]
|startingView = World
}}

*{{SVGLanguages|absolute_change_co2,_World,_1751.svg}}
{{-}}

==Data==
{{owidslidersrcs|id=gallery|widths=240|heights=240
|gallery-Asia=
File:absolute change co2, Asia, 1751.svg!year=1751
File:absolute change co2, Asia, 1752.svg!year=1752
File:absolute change co2, Asia, 1753.svg!year=1753
File:absolute change co2, Asia, 1754.svg!year=1754
File:absolute change co2, Asia, 1755.svg!year=1755
File:absolute change co2, Asia, 1756.svg!year=1756
File:absolute change co2, Asia, 1757.svg!year=1757
File:absolute change co2, Asia, 1758.svg!year=1758
File:absolute change co2, Asia, 1759.svg!year=1759
File:absolute change co2, Asia, 1760.svg!year=1760
File:absolute change co2, Asia, 1761.svg!year=1761
}}
"""


def test_titles_task_success():

    data = ExtractSteps.extract_titles(WIKITEXT)

    assert data.success is True
    assert data.main_title == "absolute change co2, World, 1751.svg"
    assert len(data.titles) == 12
    assert "absolute change co2, World, 2024 (cropped).svg" in data.titles
