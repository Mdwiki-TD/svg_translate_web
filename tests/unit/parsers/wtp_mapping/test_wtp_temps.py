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
