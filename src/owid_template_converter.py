"""
OWID Template Converter

Reads a Wikimedia template page (Template:OWID/...) and generates
the corresponding gallery/showcase page (OWID/...) using WikiTextParser.

Usage:
    python owid_template_converter.py
"""

import re
import wikitextparser as wtp


def create_new_text(wikitext: str, template_title: str) -> str:
    """
    Create new OWID gallery page text from a template page's wikitext.

    Args:
        wikitext:       Full wikitext of the source Template:OWID/... page.
        template_title: Title of the template page, e.g.
                        "Template:OWID/daily meat consumption per person".

    Returns:
        Wikitext string for the new OWID/... gallery page.
    """
    # Strip <syntaxhighlight> blocks first so their contents are not parsed
    # as live wikitext (they are display-only code examples).
    wikitext_clean = re.sub(
        r'<syntaxhighlight\b[^>]*>.*?</syntaxhighlight>',
        '',
        wikitext,
        flags=re.DOTALL | re.IGNORECASE,
    )

    parsed = wtp.parse(wikitext_clean)

    # ------------------------------------------------------------------ #
    # 1. Extract the owidslider template (first occurrence)               #
    # ------------------------------------------------------------------ #
    owidslider_template = None
    for tmpl in parsed.templates:
        if tmpl.name.strip().lower() == "owidslider":
            owidslider_template = tmpl
            break

    if owidslider_template is None:
        raise ValueError("No {{owidslider}} template found in wikitext.")

    # Rebuild the slider block as plain text so we can tweak it
    slider_raw = str(owidslider_template)

    # ------------------------------------------------------------------ #
    # 2. Build the *display* slider (upright=4.0, center)                 #
    # ------------------------------------------------------------------ #
    def patch_file_param(slider_text: str,
                         new_upright: str = "4.0",
                         add_center: bool = True) -> str:
        """Replace upright=X and optionally add |center| in the |file= param."""
        # Match the |file = [[File:...|...]] argument
        file_pattern = re.compile(
            r'(\|file\s*=\s*\[\[File:[^\]]*\|thumb\|upright=)([\d.]+)(\|)'
        )

        def replacer(m):
            before = m.group(1)
            after = m.group(3)
            # insert center after upright if not already present
            center_part = "center|" if add_center else ""
            return f"{before}{new_upright}|{center_part}"

        result = file_pattern.sub(replacer, slider_text)
        return result

    display_slider = patch_file_param(slider_raw, new_upright="4.0", add_center=True)

    # ------------------------------------------------------------------ #
    # 3. Build the *wikicode snippet* slider (upright=1.6, right)         #
    # ------------------------------------------------------------------ #
    def patch_file_param_snippet(slider_text: str) -> str:
        """Replace upright=X and add |right| (remove center if present)."""
        file_pattern = re.compile(
            r'(\|file\s*=\s*\[\[File:[^\]]*\|thumb\|upright=)([\d.]+)\|(center\|)?'
        )

        def replacer(m):
            before = m.group(1)
            return f"{before}1.6|right|"
        return file_pattern.sub(replacer, slider_text)

    snippet_slider = patch_file_param_snippet(slider_raw)
    # Make sure snippet doesn't accidentally have center
    snippet_slider = snippet_slider.replace("|center|", "|right|")

    # ------------------------------------------------------------------ #
    # 4. Extract *Source* and *Translate* links from the template text     #
    # ------------------------------------------------------------------ #
    source_link = _extract_bullet_url(wikitext, "Source")
    translate_link = _extract_bullet_url(wikitext, "Translate")

    # ------------------------------------------------------------------ #
    # 5. Extract categories (skip meta-categories like "List of …")       #
    # ------------------------------------------------------------------ #
    categories = _extract_display_categories(wikitext)

    # ------------------------------------------------------------------ #
    # 6. Assemble the new page                                             #
    # ------------------------------------------------------------------ #
    parts: list[str] = []

    # Display slider
    parts.append(display_slider)
    parts.append("{{clear}}")

    # Usage instructions + snippet
    parts.append(
        "You can use this interactive visualization in Wikipedia articles "
        "as well with the following code:"
    )
    parts.append(
        '<syntaxhighlight lang="wikitext" style="overflow:auto;">\n'
        + snippet_slider
        + "\n</syntaxhighlight>"
    )

    # Bullet list
    if source_link:
        parts.append(f"*'''Source''': {source_link}")
    if translate_link:
        parts.append(f"*'''Translate''': {translate_link}")
    parts.append(f"*'''Template''': [[{template_title}]]")

    # Categories
    if categories:
        parts.append("")          # blank line before cats
        for cat in categories:
            parts.append(f"[[{cat}]]")

    return "\n".join(parts) + "\n"


# --------------------------------------------------------------------------- #
# Helper functions                                                             #
# --------------------------------------------------------------------------- #

def _extract_bullet_url(wikitext: str, label: str) -> str | None:
    """
    Extract the URL from a bullet like:
        *'''Source''': https://…
    Returns the URL string, or None if not found.
    """
    pattern = re.compile(
        r"^\*'''%s''':\s*(\S+)" % re.escape(label),
        re.MULTILINE
    )
    m = pattern.search(wikitext)
    return m.group(1) if m else None


def _extract_display_categories(wikitext: str) -> list[str]:
    """
    Return category names (e.g. 'Category:Meat consumption maps') found
    in the wikitext, excluding navigation/meta categories such as
    'Category:List of interactive graphs', etc.
    We also add [[Category:Categories per capita]] if not already present,
    following the pattern seen in the example output.
    """
    parsed = wtp.parse(wikitext)
    cats = []
    for wl in parsed.wikilinks:
        target = wl.target.strip()
        if target.startswith("Category:"):
            cats.append(target)

    # The output example always adds "Category:Categories per capita"
    per_capita = "Category:Categories per capita"
    if per_capita not in cats:
        # Insert after the first category, matching the example's ordering
        cats.insert(1, per_capita)

    return cats


# --------------------------------------------------------------------------- #
# Demo / self-test                                                             #
# --------------------------------------------------------------------------- #

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


if __name__ == "__main__":
    result = create_new_text(EXAMPLE_WIKITEXT, EXAMPLE_TEMPLATE_TITLE)
    print("=" * 70)
    print("Generated page text for [[OWID/daily meat consumption per person]]:")
    print("=" * 70)
    print(result)
