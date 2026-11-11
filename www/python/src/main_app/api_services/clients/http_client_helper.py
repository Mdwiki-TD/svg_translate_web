"""HTTP client service for unified web requests."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

# Mapping exceptions for lang_to_wikisite_code
WIKI_SITE_EXCEPTIONS: dict[str, str] = {
    "be-tarask": "be_x_oldwiki",
    "zh-classical": "zh_classicalwiki",
    "zh-min-nan": "zh_min_nanwiki",
    "zh-yue": "zh_yuewiki",
}
NAMESPACE_TEMPLATE_PREFIX = "Template:"


class HttpHelper:
    @staticmethod
    def get_request_title(
        norm_map: dict[str, str],
        redir_map: dict[str, str],
        title: str,
    ) -> str:
        request_title = redir_map.get(title, title)
        request_title = norm_map.get(request_title, request_title)
        return request_title

    @staticmethod
    def chunks(seq: Sequence, n: int) -> list[Sequence]:
        """Yield successive n-sized chunks from seq."""
        return [seq[i : i + n] for i in range(0, len(seq), n)]

    @staticmethod
    def resolve_redirect_chain(title: str, mapping: dict[str, str]) -> str:
        """Follow redirect chain in mapping until target stabilizes, with cycle protection."""
        curr = title
        visited = set()
        while curr in mapping and curr not in visited:
            visited.add(curr)
            curr = mapping[curr]
        return curr

    @staticmethod
    def lang_to_wikisite_code(lang: str) -> str:
        """Convert language code to MediaWiki site id (e.g. 'ar' -> 'arwiki')."""
        lang_clean = lang.strip().lower()
        if lang_clean in WIKI_SITE_EXCEPTIONS:
            return WIKI_SITE_EXCEPTIONS[lang_clean]
        return f"{lang_clean.replace('-', '_')}wiki"

    @staticmethod
    def strip_ns(title: str) -> str:
        """Strip namespace prefix (e.g., 'Template:X' or 'قالب:X' -> 'X')."""
        if ":" in title:
            return title.split(":", 1)[1].strip()
        return title.strip()

    @staticmethod
    def add_template_ns(title: str) -> str:
        return f"{NAMESPACE_TEMPLATE_PREFIX}{title}"

    @classmethod
    def solve_normalized_titles(
        cls,
        normalized: list[dict],
        redirects: list[dict],
        pages_dict: dict[str, Any],
    ):
        # The requset title is "template:citeweb", and the result title is  "Template:Cite web"
        # "pages": { "1252907": { "title": "Template:Cite web", ... }
        # "normalized": [ { "fromencoded": false, "from": "template:citeweb", "to": "Template:Citeweb" } ]
        # "redirects": [ { "from": "Template:Citeweb", "to": "Template:Cite web" } ]

        norm_map = {n["to"]: n["from"] for n in normalized}
        redir_map = {r["to"]: r["from"] for r in redirects}

        data = {}

        for title, item in pages_dict.items():
            if title in redir_map:
                item["is_redirect"] = True

            request_title = cls.get_request_title(norm_map, redir_map, title)
            data[request_title] = item

        return data


__all__ = [
    "HttpHelper",
]
