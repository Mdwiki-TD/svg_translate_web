""" """

from __future__ import annotations
import wikitextparser as wtp
from src.main_app.parsers.wtp_mapping.wtp_temps import WtpTemplates

# ---------------- WtpTemplates ----------------


class TestWtpTemplates:
    def test_top_tpls_excludes_nested_and_templates_inside_refs(self):
        text = "{{Outer|x={{Inner}}}} text<ref>{{cite web|url=u}}</ref>"
        tpls = WtpTemplates.load(text)
        assert len(tpls.top_tpls) == 1
        start, end = tpls.top_tpls[0]
        assert text[start:end] == "{{Outer|x={{Inner}}}}"

    def test_contains(self):
        text = "{{T|a<ref name=A>x</ref>}} body<ref name=B>y</ref>"
        tpls = WtpTemplates.load(text)
        refs = tpls.parsed.get_tags("ref")
        assert tpls.contains(refs[0].span) is True
        assert tpls.contains(refs[1].span) is False

    def test_no_templates(self):
        assert WtpTemplates.load("plain text").top_tpls == []


class TestRenderPretty:
    def test_named_parameters_on_separate_lines(self):
        tpl = wtp.Template("{{t|a=1|b=2}}")
        assert WtpTemplates.render_pretty(tpl) == "{{t\n|a=1\n|b=2\n}}"

    def test_positional_parameters_stay_inline(self):
        tpl = wtp.Template("{{t|x|k=v}}")
        assert WtpTemplates.render_pretty(tpl) == "{{t|x\n|k=v\n}}"

    def test_ljust_pads_names(self):
        tpl = wtp.Template("{{t|a=1|bb=2}}")
        assert WtpTemplates.render_pretty(tpl, ljust=3) == "{{t\n|a  =1\n|bb =2\n}}"

    def test_ljust_zero_means_no_padding(self):
        tpl = wtp.Template("{{t|a=1}}")
        assert WtpTemplates.render_pretty(tpl, ljust=0) == "{{t\n|a=1\n}}"

    def test_no_parameters(self):
        tpl = wtp.Template("{{t}}")
        assert WtpTemplates.render_pretty(tpl) == "{{t\n}}"

    def test_trims_name_and_values(self):
        tpl = wtp.Template("{{ t | a = 1 }}")
        assert WtpTemplates.render_pretty(tpl) == "{{t\n|a=1\n}}"

    def test_does_not_mutate_template(self):
        parsed = wtp.parse("{{t|a=1}}")
        tpl = parsed.templates[0]

        WtpTemplates.render_pretty(tpl, ljust=5)
        assert parsed.string == "{{t|a=1}}"
