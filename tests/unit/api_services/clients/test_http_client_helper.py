"""Unit tests for Citation Templates models and service with batch processing."""

from __future__ import annotations

import copy

import pytest
from src.main_app.api_services.clients.http_client_helper import HttpHelper


def build_maps(normalized=None, redirects=None):
    """Build reverse maps (to -> from) the same way the API response is consumed."""
    norm_map = {n["to"]: n["from"] for n in normalized or []}
    redir_map = {r["to"]: r["from"] for r in redirects or []}
    return norm_map, redir_map


class TestGetRequestTitle:
    # ---------- Core scenarios ----------

    def test_basic(self):
        request_title = "template:citeweb"
        result_title = "Template:Cite web"

        # Request: "template:citeweb" -> normalized "Template:Citeweb"
        # -> redirected to "Template:Cite web"
        norm_map, redir_map = build_maps(
            normalized=[{"from": "template:citeweb", "to": "Template:Citeweb"}],
            redirects=[{"from": "Template:Citeweb", "to": "Template:Cite web"}],
        )

        assert HttpHelper.get_request_title(norm_map, redir_map, result_title) == request_title

    def test_only_normalized(self):
        norm_map, _ = build_maps(
            normalized=[{"from": "template:cite web", "to": "Template:Cite web"}],
        )

        result = HttpHelper.get_request_title(norm_map, {}, "Template:Cite web")

        assert result == "template:cite web"

    def test_only_redirect(self):
        _, redir_map = build_maps(
            redirects=[{"from": "Old title", "to": "New title"}],
        )

        result = HttpHelper.get_request_title({}, redir_map, "New title")

        assert result == "Old title"

    def test_no_maps_returns_title_unchanged(self):
        assert HttpHelper.get_request_title({}, {}, "Some page") == "Some page"

    # ---------- Title not present in the maps ----------

    def test_title_not_in_any_map_returns_title(self):
        norm_map, redir_map = build_maps(
            normalized=[{"from": "a b", "to": "A b"}],
            redirects=[{"from": "X", "to": "Y"}],
        )

        assert HttpHelper.get_request_title(norm_map, redir_map, "Unrelated") == "Unrelated"

    def test_unrelated_entries_do_not_affect_result(self):
        norm_map, redir_map = build_maps(
            normalized=[
                {"from": "foo bar", "to": "Foo bar"},
                {"from": "baz", "to": "Baz"},
            ],
            redirects=[
                {"from": "Alpha", "to": "Beta"},
                {"from": "Gamma", "to": "Delta"},
            ],
        )

        assert HttpHelper.get_request_title(norm_map, redir_map, "Delta") == "Gamma"
        assert HttpHelper.get_request_title(norm_map, redir_map, "Baz") == "baz"
        assert HttpHelper.get_request_title(norm_map, redir_map, "Beta") == "Alpha"

    # ---------- Multiple entries in a single response ----------

    def test_multiple_titles_resolved_independently(self):
        norm_map, redir_map = build_maps(
            normalized=[
                {"from": "template:citeweb", "to": "Template:Citeweb"},
                {"from": "template:infobox", "to": "Template:Infobox"},
            ],
            redirects=[
                {"from": "Template:Citeweb", "to": "Template:Cite web"},
            ],
        )

        assert HttpHelper.get_request_title(norm_map, redir_map, "Template:Cite web") == "template:citeweb"
        assert HttpHelper.get_request_title(norm_map, redir_map, "Template:Infobox") == "template:infobox"

    # ---------- Order of resolution ----------

    def test_redirect_is_applied_before_normalization(self):
        # The redirect result must be fed into the normalization map,
        # not the other way around.
        norm_map = {"B": "b"}
        redir_map = {"C": "B"}

        assert HttpHelper.get_request_title(norm_map, redir_map, "C") == "b"

    def test_normalization_key_equal_to_title_but_redirect_exists(self):
        # "B" exists in both maps; redirect wins first and then its output is normalized.
        norm_map = {"A": "a", "B": "b"}
        redir_map = {"B": "A"}

        assert HttpHelper.get_request_title(norm_map, redir_map, "B") == "a"

    def test_only_one_redirect_hop_is_followed(self):
        # Documents current behavior: chained redirects (C -> B -> A) are not resolved
        # recursively, only a single hop is followed.
        redir_map = {"C": "B", "B": "A"}

        assert HttpHelper.get_request_title({}, redir_map, "C") == "B"

    def test_only_one_normalization_hop_is_followed(self):
        norm_map = {"C": "B", "B": "A"}

        assert HttpHelper.get_request_title(norm_map, {}, "C") == "B"

    # ---------- Edge cases ----------

    def test_empty_title(self):
        assert HttpHelper.get_request_title({}, {}, "") == ""

    def test_empty_title_present_in_map(self):
        assert HttpHelper.get_request_title({"": "x"}, {}, "") == "x"

    def test_lookup_is_case_sensitive(self):
        norm_map = {"Template:Cite web": "template:cite web"}

        assert HttpHelper.get_request_title(norm_map, {}, "template:Cite web") == ("template:Cite web")

    def test_whitespace_is_significant(self):
        norm_map = {"Cite web": "cite web"}

        assert HttpHelper.get_request_title(norm_map, {}, "Cite web ") == "Cite web "
        assert HttpHelper.get_request_title(norm_map, {}, "Cite web") == "cite web"

    def test_underscores_and_spaces_are_distinct(self):
        norm_map = {"Cite web": "cite_web"}

        assert HttpHelper.get_request_title(norm_map, {}, "Cite_web") == "Cite_web"
        assert HttpHelper.get_request_title(norm_map, {}, "Cite web") == "cite_web"

    def test_unicode_arabic_titles(self):
        norm_map, redir_map = build_maps(
            normalized=[{"from": "قالب:استشهاد بويب", "to": "قالب:استشهاد بويب"}],
            redirects=[{"from": "قالب:استشهاد", "to": "قالب:استشهاد بويب"}],
        )

        result = HttpHelper.get_request_title(norm_map, redir_map, "قالب:استشهاد بويب")

        assert result == "قالب:استشهاد"

    def test_identity_mapping_returns_same_title(self):
        norm_map = {"Page": "Page"}
        redir_map = {"Page": "Page"}

        assert HttpHelper.get_request_title(norm_map, redir_map, "Page") == "Page"

    # ---------- Behavior guarantees ----------

    def test_does_not_mutate_inputs(self):
        norm_map, redir_map = build_maps(
            normalized=[{"from": "a", "to": "A"}],
            redirects=[{"from": "A", "to": "B"}],
        )
        norm_before = copy.deepcopy(norm_map)
        redir_before = copy.deepcopy(redir_map)

        HttpHelper.get_request_title(norm_map, redir_map, "B")

        assert norm_map == norm_before
        assert redir_map == redir_before

    def test_returns_str(self):
        assert isinstance(HttpHelper.get_request_title({}, {}, "X"), str)

    def test_is_deterministic(self):
        norm_map, redir_map = build_maps(
            normalized=[{"from": "a", "to": "A"}],
            redirects=[{"from": "A", "to": "B"}],
        )

        results = {HttpHelper.get_request_title(norm_map, redir_map, "B") for _ in range(5)}

        assert results == {"a"}

    # ---------- Parametrized table of cases ----------

    @pytest.mark.parametrize(
        ("normalized", "redirects", "result_title", "expected"),
        [
            # no changes at all
            ([], [], "Page", "Page"),
            # normalization only
            ([{"from": "page", "to": "Page"}], [], "Page", "page"),
            # redirect only
            ([], [{"from": "Old", "to": "New"}], "New", "Old"),
            # normalization + redirect
            (
                [{"from": "old", "to": "Old"}],
                [{"from": "Old", "to": "New"}],
                "New",
                "old",
            ),
            # redirect target is not the requested result title
            (
                [{"from": "old", "to": "Old"}],
                [{"from": "Old", "to": "New"}],
                "Other",
                "Other",
            ),
            # namespace normalization
            (
                [{"from": "category:foo", "to": "Category:Foo"}],
                [],
                "Category:Foo",
                "category:foo",
            ),
        ],
    )
    def test_parametrized(self, normalized, redirects, result_title, expected):
        norm_map, redir_map = build_maps(normalized, redirects)

        assert HttpHelper.get_request_title(norm_map, redir_map, result_title) == expected


class TestCitationTemplatesServiceHelpers:
    """Test helper functions like chunks, strip_ns, follow, and lang_to_wikisite_code."""

    def test_strip_ns(self):
        assert HttpHelper.strip_ns("Template:Cite web") == "Cite web"
        assert HttpHelper.strip_ns("قالب:استشهاد بكتاب") == "استشهاد بكتاب"
        assert HttpHelper.strip_ns("NoNs") == "NoNs"

    def test_follow_redirects(self):
        mapping = {"A": "B", "B": "C", "C": "D"}
        assert HttpHelper.resolve_redirect_chain("A", mapping) == "D"
        assert HttpHelper.resolve_redirect_chain("Z", mapping) == "Z"

        # Cycle protection
        cycle_map = {"A": "B", "B": "A"}
        assert HttpHelper.resolve_redirect_chain("A", cycle_map) in ("A", "B")

    def test_lang_to_wikisite(self):
        assert HttpHelper.lang_to_wikisite_code("ar") == "arwiki"
        assert HttpHelper.lang_to_wikisite_code("en") == "enwiki"
        assert HttpHelper.lang_to_wikisite_code("be-tarask") == "be_x_oldwiki"
        assert HttpHelper.lang_to_wikisite_code("zh-yue") == "zh_yuewiki"
        assert HttpHelper.lang_to_wikisite_code("simple") == "simplewiki"
