"""Generic utilities for adding/updating templates inside the ``other versions``
parameter of a main template (e.g. ``{{Information}}``) in wikitext."""

from __future__ import annotations

import logging
from typing import Callable, Iterable

import wikitextparser as wtp

logger = logging.getLogger(__name__)


class OtherVersionsUpdater:
    """Adds or updates templates inside the "other versions" parameter.

    Two generic operations are supported, and new template types can be
    supported by adding a thin method on top of them:

    * :meth:`merge_values`: a template whose positional parameters are a
      list of values (``{{Svg lang|ar|de|fr}}``). New values are merged into
      the existing template instead of adding a second one.
    * :meth:`add_template`: a single-instance template with ``1=`` value
      (``{{Extracted from|1=File.svg}}``). Skipped if already present.

    Example::

        updater = OtherVersionsUpdater()
        text = updater.add_svg_langs(text, ["ar", "de"])
        text = updater.add_template(text, "Extracted from", "Original.svg")

    Args:
        main_template_name: Template that owns the parameter.
        param_names: Accepted parameter names (the first is used when the
            parameter has to be created). Matching ignores case and
            treats ``_`` as a space.
        case_insensitive: Whether duplicate detection ignores case.
    """

    DEFAULT_MAIN_TEMPLATE = "Information"
    DEFAULT_PARAM_NAMES: tuple[str, ...] = ("other versions", "other_versions")

    def __init__(
        self,
        main_template_name: str = DEFAULT_MAIN_TEMPLATE,
        param_names: Iterable[str] | None = None,
        case_insensitive: bool = True,
    ) -> None:
        self.main_template_name = main_template_name
        self.param_names = list(param_names) if param_names else list(self.DEFAULT_PARAM_NAMES)
        self.case_insensitive = case_insensitive

    # ---------------------------------------------------------------- #
    # Public API
    # ---------------------------------------------------------------- #

    def merge_values(
        self,
        text: str,
        template_name: str,
        values: Iterable[str],
        *,
        sort: bool = False,
    ) -> str:
        """Merge ``values`` into ``{{template_name|v1|v2|...}}``.

        Creates the template (and the parameter) if missing, otherwise adds
        only the values that are not already present, keeping the existing
        order. Returns ``text`` unchanged when nothing needs to change or
        the main template is not found.
        """
        clean = [v.strip() for v in values if v and v.strip()]
        if not clean:
            return text
        return self._update(text, lambda cur: self._merge_positional(cur, template_name, clean, sort))

    def add_template(self, text: str, template_name: str, first_param_value: str) -> str:
        """Append ``{{template_name|1=first_param_value}}`` unless already present."""
        return self._update(text, lambda cur: self._append_unique(cur, template_name, first_param_value))

    # ---- presets (add more here for other templates) ---------------- #

    def add_svg_langs(self, text: str, langs: Iterable[str], *, sort: bool = False) -> str:
        """Add language codes to ``{{Svg lang|...}}``."""
        return self.merge_values(text, "Svg lang", (lang.lower() for lang in langs if lang), sort=sort)

    # ---------------------------------------------------------------- #
    # Core
    # ---------------------------------------------------------------- #

    def _update(self, text: str, transform: Callable[[str], str]) -> str:
        parsed = wtp.parse(text)
        main = self._find_main_template(parsed)
        if main is None:
            logger.debug("Main template %r not found", self.main_template_name)
            return text

        arg = self._find_param(main)
        raw = arg.value if arg else ""
        current = raw.strip()

        new_value = transform(current)
        if new_value == current:
            return text

        if arg:
            if current:
                lead = raw[: len(raw) - len(raw.lstrip())]
                trail = raw[len(raw.rstrip()):]
            else:
                lead, trail = " ", "\n"
            arg.value = f"{lead}{new_value}{trail}"
        else:
            main.set_arg(self.param_names[0], new_value)
        return parsed.string

    # ---------------------------------------------------------------- #
    # Transforms (operate on the parameter value only)
    # ---------------------------------------------------------------- #

    def _merge_positional(self, current: str, template_name: str, values: list[str], sort: bool) -> str:
        tpl = self._find_template(current, template_name)

        if tpl is None:
            merged = self._dedupe(values)
            if sort:
                merged.sort(key=self._key)
            new_tpl = self._render(template_name, merged, [])
            return f"{current}\n{new_tpl}" if current else new_tpl

        existing: list[tuple[int, str]] = []
        named: list[str] = []
        for a in tpl.arguments:
            name = a.name.strip()
            value = a.value.strip()
            if name.isdigit():
                if value:
                    existing.append((int(name), value))
            else:
                named.append(f"{name}={a.value}")

        old = [v for _, v in sorted(existing)]
        merged = self._dedupe(old + values)
        if len(merged) == len(self._dedupe(old)):
            return current  # nothing new
        if sort:
            merged.sort(key=self._key)

        new_tpl = self._render(tpl.name.strip(), merged, named)
        return current.replace(tpl.string, new_tpl, 1)

    def _append_unique(self, current: str, template_name: str, first_param_value: str) -> str:
        new_tpl = f"{{{{{template_name}|1={first_param_value}}}}}"
        if not current:
            return new_tpl

        wanted = self._key(first_param_value)
        for t in wtp.parse(current).templates:
            if self._norm_name(t.name) != self._norm_name(template_name):
                continue
            arg = next((a for a in t.arguments if a.name.strip() == "1"), None)
            if arg and self._key(arg.value) == wanted:
                return current
        return f"{current}\n{new_tpl}"

    # ---------------------------------------------------------------- #
    # Helpers
    # ---------------------------------------------------------------- #

    def _find_main_template(self, parsed: wtp.WikiText) -> wtp.Template | None:
        target = self._norm_name(self.main_template_name)
        for t in parsed.templates:
            if self._norm_name(t.name) == target:
                return t
        return None

    def _find_param(self, template: wtp.Template) -> wtp.Argument | None:
        return self._get_argument(template, self.param_names)

    @staticmethod
    def _get_argument(template: wtp.Template, params: Iterable[str]) -> wtp.Argument | None:
        """Return the first argument matching one of ``params`` (in order).

        Matching ignores case and surrounding spaces, and treats ``_`` as a space.
        """
        args_map = {OtherVersionsUpdater._norm_name(a.name): a for a in template.arguments}
        for param in params:
            found = args_map.get(OtherVersionsUpdater._norm_name(param))
            if found:
                return found
        return None

    def _find_template(self, value: str, name: str) -> wtp.Template | None:
        target = self._norm_name(name)
        for t in wtp.parse(value).templates:
            if self._norm_name(t.name) == target:
                return t
        return None

    def _dedupe(self, values: Iterable[str]) -> list[str]:
        seen: dict[str, str] = {}
        for v in values:
            seen.setdefault(self._key(v), v)
        return list(seen.values())

    def _key(self, value: str) -> str:
        result = value.replace("_", " ").strip()
        return result.lower() if self.case_insensitive else result

    @staticmethod
    def _norm_name(name: str) -> str:
        return name.replace("_", " ").strip().lower()

    @staticmethod
    def _render(name: str, positional: list[str], named: list[str]) -> str:
        return "{{" + "|".join([name, *positional, *named]) + "}}"


def add_other_versions_new(
    *,
    text: str,
    temp_name: str,
    first_param_valve: str,  # name kept for backward compatibility
    main_template_name: str = "Information",
    main_template_args: list[str] | None = None,
) -> str:
    """Backward-compatible wrapper: add ``{{temp_name|1=value}}`` to other versions."""
    updater = OtherVersionsUpdater(
        main_template_name=main_template_name,
        param_names=main_template_args,
    )
    return updater.add_template(text, temp_name, first_param_valve)


def add_svg_langs_to_other_versions(*, text: str, langs: list[str]) -> str:
    """Functional wrapper around :meth:`OtherVersionsUpdater.add_svg_langs`."""
    return OtherVersionsUpdater().add_svg_langs(text, langs)

OtherVersionsAdder = OtherVersionsUpdater

__all__ = [
    "OtherVersionsUpdater",
    "add_other_versions_new",
    "add_svg_langs_to_other_versions",
]
