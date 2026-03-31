import re

RE_SVG_LANG = re.compile(r"\{\{\s*SVGLanguages\s*\|\s*([^}|]+)", re.I)
# *'''Translate''': https://svgtranslate.toolforge.org/File:share_with_mental_and_substance_disorders,_World,_1990.svg
RE_TRANSLATE = re.compile(r"\*\s*'''Translat\w+'''\s*:\s*https://svgtranslate\.toolforge\.org/File:([^ \n]+)", re.I)


def load_link_file_name(text) -> str | None:
    trans_match = RE_TRANSLATE.search(text)
    if trans_match:
        return trans_match.group(1).strip()

    return None


def add_template_to_text(text, template_text) -> str:
    if not RE_TRANSLATE.search(text):
        return text

    return re.sub(RE_TRANSLATE, lambda m: m.group(0) + "\n*" + template_text, text, count=1)
