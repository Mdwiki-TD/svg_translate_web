
from src.main_app.jobs_workers.add_svglanguages_template.utils import load_link_file_name, add_template_to_text


def test_load_link_file_name():
    wikitext = """
*[[Commons:List of interactive graphs|Return to list]]

{{owidslider
|start        = 2021
|list         = Template:OWID/share with mental and substance disorders#gallery
|location      = commons
|caption      =
|title        =
|language     =
|file         = [[File:share with mental and substance disorders, World, 2021 (cropped).svg|link=|thumb|upright=1.6|share with mental and substance disorders]]
|startingView = World
}}
<syntaxhighlight lang="wikitext" style="overflow:auto;">
{{owidslider
|start        = 2021
|list         = Template:OWID/share with mental and substance disorders#gallery
|location      = commons
|caption      =
|title        =
|language     =
|file         = [[File:share with mental and substance disorders, World, 2021 (cropped).svg|link=|thumb|upright=1.6|share with mental and substance disorders]]
|startingView = World
}}
</syntaxhighlight>
*'''Source''': https://ourworldindata.org/grapher/share-with-mental-and-substance-disorders
*'''Translate''': https://svgtranslate.toolforge.org/File:share_with_mental_and_substance_disorders,_World,_1990.svg
{{-}}
    """

    file_name = load_link_file_name(wikitext)
    expected = "share_with_mental_and_substance_disorders,_World,_1990.svg"
    assert file_name == expected
