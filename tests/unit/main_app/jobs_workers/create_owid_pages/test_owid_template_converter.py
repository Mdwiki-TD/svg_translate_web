""" """

from src.main_app.jobs_workers.create_owid_pages.owid_template_converter import create_new_text

EXAMPLE_TEMPLATE_TITLE = "Template:OWID/daily meat consumption per person"

EXAMPLE_WIKITEXT = r"""*[[Commons:List of interactive graphs|Return to list]]
[[Category:Meat consumption maps of the world]]
[[Category:Meat statistics]]
[[Category:Meat consumption maps]]
{{owidslider
|start        = 2022
|list         = Template:OWID/daily meat consumption per person#gallery
|location      = commons
|caption      =
|title        =
|language     =
|file         = [[File:daily meat consumption per person, World, 2022 (cropped).svg|link=|thumb|upright=1.6|Daily meat consumption per person]]
|startingView = World
}}
<syntaxhighlight lang="wikitext" style="overflow:auto;">
{{owidslider
|start        = 2022
|list         = Template:OWID/daily meat consumption per person#gallery
|location      = commons
|caption      =
|title        =
|language     =
|file         = [[File:daily meat consumption per person, World, 2022 (cropped).svg|link=|thumb|upright=1.6|Daily meat consumption per person]]
|startingView = World
}}
</syntaxhighlight>
*'''Source''': https://ourworldindata.org/grapher/daily-meat-consumption-per-person
*'''Translate''': https://svgtranslate.toolforge.org/File:daily_meat_consumption_per_person,_World,_1961.svg

{{-}}

==Data==
{{owidslidersrcs|id=gallery|widths=240|heights=240
|gallery-Oceania=
File:daily meat consumption per person, Oceania, 1961.svg!year=1961
File:daily meat consumption per person, Oceania, 1962.svg!year=1962
}}
"""

EXPECTED__WIKITEXT = """
{{owidslider
|start        = 2022
|list         = Template:OWID/daily meat consumption per person#gallery
|location      = commons
|caption      =
|title        =
|language     =
|file         = [[File:daily meat consumption per person, World, 2022 (cropped).svg|link=|thumb|upright=4.0|center|Daily meat consumption per person]]
|startingView = World
}}
{{clear}}
You can use this interactive visualization in Wikipedia articles as well with the following code:
<syntaxhighlight lang="wikitext" style="overflow:auto;">
{{owidslider
|start        = 2022
|list         = Template:OWID/daily meat consumption per person#gallery
|location      = commons
|caption      =
|title        =
|language     =
|file         = [[File:daily meat consumption per person, World, 2022 (cropped).svg|link=|thumb|upright=1.6|right|Daily meat consumption per person]]
|startingView = World
}}
</syntaxhighlight>
*'''Source''': https://ourworldindata.org/grapher/daily-meat-consumption-per-person
*'''Translate''': https://svgtranslate.toolforge.org/File:daily_meat_consumption_per_person,_World,_1961.svg
*{{SVGLanguages|daily_meat_consumption_per_person,_World,_1961.svg}}
*'''Template''': [[Template:OWID/daily meat consumption per person]]

[[Category:Meat consumption maps of the world]]
[[Category:Meat statistics]]
[[Category:Meat consumption maps]]
"""


def test_create_new_text():

    result = create_new_text(EXAMPLE_WIKITEXT, EXAMPLE_TEMPLATE_TITLE)
    assert result.strip() == EXPECTED__WIKITEXT.strip()
