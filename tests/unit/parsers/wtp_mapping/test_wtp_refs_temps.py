from __future__ import annotations

import wikitextparser as wtp
from src.main_app.parsers.wtp_mapping.wtp_refs_temps import WtpRefsTemps

BASIC = (
    "{{Infobox\n"
    "| a = x<ref name=A>{{cite web|url=http://a}}</ref>\n"
    "| b = y<ref name=A />\n"
    "}}\n"
    "BODY first.<ref name=A /> Second.<ref name=A />\n"
)

# ---------------- WtpRefsTemps ----------------


class TestWtpTemps:
    def test_set_arg(self):
        temp = wtp.Template("{{Svg lang|ar|de|fr}}")

        temp.set_arg("dl", "en")
        assert temp.string == "{{Svg lang|ar|de|fr|dl=en}}"

    def test_set_arg_before(self):
        temp = wtp.Template("{{Svg lang|ar|de|fr}}")

        temp.set_arg("dl", "en", before="1")
        assert temp.string == "{{Svg lang|dl=en|ar|de|fr}}"


class TestWtpRefsTemps:
    def test_template_vs_body_split(self):
        refs = WtpRefsTemps.load(BASIC)
        assert len(refs.tpl_refs) == 2
        assert len(refs.body_refs) == 2
        assert list(refs.tpl_full_refs) == ["A"]
        assert refs.body_full_refs == {}
        assert refs.body_short_names == {"A"}
