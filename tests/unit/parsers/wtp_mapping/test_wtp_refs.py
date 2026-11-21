"""
Unit tests for wtp_mapping module.
"""

import wikitextparser as wtp
from src.main_app.parsers.wtp_mapping import WtpRef, WtpRefs


class TestWtpRef:
    def test_basic(self):
        text = "<ref name = PI2022></ref>"
        result = WtpRef.load(wtp.Tag(text))
        assert result.name == "PI2022"
        assert result.is_self_closing() is True

    def test_for_bug(self) -> None:
        """
        BUG: WtpRef.from_text("<ref name = PI2022/>").name == "PI2022/" this should be fixed in WtpRef to become "PI2022"
        This bug already solved in wikitextparser>0.55
        """
        wtp_tag = wtp.Tag("<ref name = PI2022/>")
        # assert wtp_tag.attrs["name"] == "PI2022/"
        assert wtp_tag.attrs["name"] == "PI2022"

        wtp_tag = wtp.Tag("<ref name=PI2022/>")
        # this should be fixed in WtpRef to become "PI2022"
        # assert wtp_tag.attrs["name"] == "PI2022/"
        assert wtp_tag.attrs["name"] == "PI2022"

    def test_to_short(self) -> None:
        # Already self-closing tags should be returned unchanged
        for tag_str in ["<ref name=A />", '<ref name="A"/>', '<ref name="A" />']:
            ref = WtpRef.load(wtp.Tag(tag_str))
            assert ref.to_short() == tag_str

        # Tags with empty or non-empty content should be converted to self-closing tag
        ref_empty = WtpRef.load(wtp.Tag("<ref name=A></ref>"))
        assert ref_empty.to_short() == "<ref name=A />"

        ref_content = WtpRef.load(wtp.Tag("<ref name=A>x</ref>"))
        assert ref_content.to_short() == "<ref name=A />"


class TestGetAllRefs:
    """Tests for WtpRefs.load(text).all_refs function"""

    def test_single_full_ref_no_name(self):
        text = "Some text<ref>A basic citation</ref> more text"
        result = WtpRefs.load(text).all_refs

        assert len(result) == 1
        assert result[0].contents == "A basic citation"
        assert result[0].tag_str == "<ref>A basic citation</ref>"
        assert result[0].name == ""

    def test_single_full_ref_with_name(self):
        text = '<ref name="smith2020">Smith, J. (2020)</ref>'
        result = WtpRefs.load(text).all_refs

        assert len(result) == 1
        assert result[0].contents == "Smith, J. (2020)"
        assert result[0].name == "smith2020"
        assert result[0].attrs["name"] == "smith2020"
        assert result[0].tag_str == text

    def test_multiple_full_refs(self):
        text = "Text<ref>First</ref> more<ref>Second</ref>"
        result = WtpRefs.load(text).all_refs

        assert len(result) == 2
        assert result[0].contents == "First"
        assert result[1].contents == "Second"

    def test_multiple_named_refs_with_text_between(self):
        text = '<ref name="ref1">Content 1</ref> Text <ref name="ref2">Content 2</ref>'
        result = WtpRefs.load(text).all_refs

        assert len(result) == 2
        assert [c.name for c in result] == ["ref1", "ref2"]
        assert [c.contents for c in result] == ["Content 1", "Content 2"]
        assert result[0].tag_str == '<ref name="ref1">Content 1</ref>'

    def test_not_excludes_self_closing_refs(self):
        text = 'Text<ref name="a">Full ref</ref> and<ref name="a" /> a short ref'
        result = WtpRefs.load(text).all_refs

        assert len(result) == 2
        assert result[0].contents == "Full ref"
        assert result[0].name == "a"

    def test_no_refs_returns_empty_list(self):
        result = WtpRefs.load("Just some plain text without any refs").all_refs

        assert result == []

    def test_empty_text_returns_empty_list(self):
        result = WtpRefs.load("").all_refs

        assert result == []

    def test_ref_with_extra_attributes(self):
        text = '<ref name="foo" group="note">Some content</ref>'
        result = WtpRefs.load(text).all_refs

        assert len(result) == 1
        assert result[0].name == "foo"
        assert result[0].attrs["name"] == "foo"
        assert result[0].attrs["group"] == "note"

    def test_ref_name_is_stripped(self):
        text = '<ref name=" spaced ">Content</ref>'
        result = WtpRefs.load(text).all_refs

        assert len(result) == 1
        assert result[0].name == "spaced"

    def test_nested_markup_inside_ref(self):
        text = "<ref>See [[Some Page|the page]] for {{cite web|url=example.com}} details</ref>"
        result = WtpRefs.load(text).all_refs

        assert len(result) == 1
        assert "[[Some Page|the page]]" in result[0].contents
        assert "{{cite web|url=example.com}}" in result[0].contents

    def test_multiline_ref_content(self):
        text = "<ref>Line one\nLine two\nLine three</ref>"
        result = WtpRefs.load(text).all_refs

        assert len(result) == 1
        assert result[0].contents == "Line one\nLine two\nLine three"

    def test_duplicate_names_both_returned(self):
        text = '<ref name="dup">First</ref> text <ref name="dup">Second</ref>'
        result = WtpRefs.load(text).all_refs

        assert len(result) == 2
        assert [c.contents for c in result] == ["First", "Second"]
        assert all(c.name == "dup" for c in result)


class TestGetShortRefs:
    """Tests for WtpRefs.load(text).short_refs function"""

    def test_single_short_ref(self):
        text = '<ref name="smith2020" />'
        result = WtpRefs.load(text).short_refs

        assert len(result) == 1
        assert result[0].name == "smith2020"
        assert result[0].contents == ""
        assert result[0].tag_str == '<ref name="smith2020" />'

    def test_multiple_short_refs(self):
        # Mixes the "/>" and " />" self-closing styles
        text = 'Text<ref name="a"/> more<ref name="b" />'
        result = WtpRefs.load(text).short_refs

        assert len(result) == 2
        assert {c.name for c in result} == {"a", "b"}
        assert all(c.contents == "" for c in result)

    def test_excludes_full_refs(self):
        text = '<ref name="full">Full content</ref><ref name="short" />'
        result = WtpRefs.load(text).short_refs

        assert len(result) == 1
        assert result[0].name == "short"

    def test_no_refs_returns_empty_list(self):
        result = WtpRefs.load("No refs in this text").short_refs

        assert result == []

    def test_empty_text_returns_empty_list(self):
        result = WtpRefs.load("").short_refs

        assert result == []

    def test_short_ref_without_name(self):
        text = "<ref />"
        result = WtpRefs.load(text).short_refs

        assert len(result) == 1
        assert result[0].name == ""
        assert result[0].contents == ""

    def test_short_ref_name_is_stripped(self):
        text = '<ref name=" spaced " />'
        result = WtpRefs.load(text).short_refs

        assert len(result) == 1
        assert result[0].name == "spaced"

    def test_short_ref_with_extra_attributes(self):
        text = '<ref name="foo" group="note" />'
        result = WtpRefs.load(text).short_refs

        assert len(result) == 1
        assert result[0].attrs["name"] == "foo"
        assert result[0].attrs["group"] == "note"

    def test_no_space_before_self_close(self):
        text = '<ref name="tight"/>'
        result = WtpRefs.load(text).short_refs

        assert len(result) == 1
        assert result[0].name == "tight"
        assert result[0].tag_str == '<ref name="tight"/>'


class TestGetFullRefs:
    """Tests for WtpRefs.full_refs"""

    def test_single_named_ref(self):
        text = '<ref name="smith2020">Smith, J. (2020)</ref>'
        result = WtpRefs.load(text).full_refs

        assert len(result) == 1
        assert result[0].name == "smith2020"
        assert result[0].tag_str == '<ref name="smith2020">Smith, J. (2020)</ref>'

    def test_multiple_named_refs(self):
        text = '<ref name="a">First</ref> text <ref name="b">Second</ref>'
        result = WtpRefs.load(text).full_refs

        assert [x.name for x in result] == ["a", "b"]
        assert result[0].tag_str == '<ref name="a">First</ref>'
        assert result[1].tag_str == '<ref name="b">Second</ref>'

    def test_unnamed_refs_excluded(self):
        text = '<ref>No name here</ref><ref name="named">Has name</ref>'
        result = WtpRefs.load(text).full_named_refs

        assert len(result) == 1
        assert result[0].name == "named"

    def test_self_closing_refs_excluded(self):
        text = '<ref name="full">Full ref</ref><ref name="short" />'
        result = WtpRefs.load(text).full_refs

        assert [x.name for x in result] == ["full"]
        assert result[0].tag_str == '<ref name="full">Full ref</ref>'

    def test_short_ref_before_full_ref_with_same_name(self):
        # A short ref appearing first must not shadow the full definition
        text = '<ref name="ref2"/><ref name="ref1">Content 1</ref> <ref name="ref2">Content 2</ref>'
        result = WtpRefs.load(text).full_refs

        assert [x.name for x in result] == ["ref1", "ref2"]
        assert result[0].tag_str == '<ref name="ref1">Content 1</ref>'
        assert result[1].tag_str == '<ref name="ref2">Content 2</ref>'

    def test_only_short_refs_returns_empty_list(self):
        result = WtpRefs.load('<ref name="ref2"/>').full_refs

        assert result == []

    def test_no_refs_returns_empty_list(self):
        result = WtpRefs.load("Plain text, no refs at all").full_refs

        assert result == []

    def test_empty_text_returns_empty_list(self):
        result = WtpRefs.load("").full_refs

        assert result == []

    def test_duplicate_names_are_all_kept_in_order(self):
        # full_refs is a list, so no "last wins" de-duplication happens here
        text = '<ref name="dup">First</ref> text <ref name="dup">Second</ref>'
        result = WtpRefs.load(text).full_refs

        assert [x.name for x in result] == ["dup", "dup"]
        assert result[0].tag_str == '<ref name="dup">First</ref>'
        assert result[1].tag_str == '<ref name="dup">Second</ref>'


class TestGetShortAndFullRefs:
    def test_refs(self, load_fixture) -> None:
        source = load_fixture("unit/parsers/wtp_mapping/data/source-1.wiki")

        full_refs = WtpRefs.load(source).full_refs
        full_named_refs = WtpRefs.load(source).full_named_refs
        full_refs_keys = {x.name for x in full_refs}

        assert full_refs_keys == {
            "",
            "AHFS2022",
            "BNF81",
            "EMA",
            "EMC",
            "EPAR2022",
            "Lin",
            "MSR",
            "Minkovsky",
            "PI2022",
            "TGA",
            "WHO22nd",
        }

        short_refs = WtpRefs.load(source).short_refs
        short_refs_by_name = {x.name: x for x in short_refs}

        assert set(short_refs_by_name.keys()) == {
            "AHFS2022",
            "BNF81",
            "EMA",
            "EMC",
            "EPAR2022",
            "Lin",
            "Minkovsky",
            "PI2022",
            "TGA",
            "not_exists_ref_should_be_deleted",
        }

        assert len(full_refs) == 13
        assert len(full_named_refs) == 11
        assert len(short_refs) == 22


# ---------------- WtpRefs ----------------


BASIC = (
    "{{Infobox\n"
    "| a = x<ref name=A>{{cite web|url=http://a}}</ref>\n"
    "| b = y<ref name=A />\n"
    "}}\n"
    "BODY first.<ref name=A /> Second.<ref name=A />\n"
)


class TestWtpRefs:
    def test_full_and_short_collection(self):
        refs = WtpRefs.load(BASIC)
        full_reference_list = [x for x in refs.full_refs if x.name == "A"]
        assert full_reference_list[0].name == "A"
        assert full_reference_list[0].tag_str == "<ref name=A>{{cite web|url=http://a}}</ref>"

        short_reference_list = [x for x in refs.short_refs if x.name == "A"]
        assert len(short_reference_list) == 3

    def test_unnamed_refs_are_skipped(self):
        refs = WtpRefs.load("{{T|a<ref>no name</ref>}}")
        assert refs.full_named_refs == []
        assert refs.short_refs == []
        assert len(refs.full_refs) == 1

    def test_name_with_quotes_is_normalized(self):
        refs = WtpRefs.load("text<ref name='A'>c</ref>")
        full_reference_list = [x for x in refs.full_refs if x.name == "A"]
        assert len(full_reference_list) == 1
        assert full_reference_list[0].contents == "c"
