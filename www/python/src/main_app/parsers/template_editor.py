"""Generic, reusable editor for templates inside a wikitext fragment.

Every method takes a wikitext string and returns a new string, so the class
has no state besides its comparison settings and works with any template.
"""

from __future__ import annotations

from typing import Literal

import wikitextparser as wtp


class TemplateEditor:
    """Add / merge / replace / delete operations on templates in wikitext.

    Example::

        editor = TemplateEditor()
        text = editor.merge_positional(text, "Svg lang", ["ar", "de"])
        text = editor.ensure_named(text, "Svg lang", "dl", "en")
        text = editor.add_unique(text, "Extracted from", "Original.svg")

    Args:
        case_insensitive: Whether value comparison (duplicates, deletion)
            ignores case. Template and parameter names are always compared
            ignoring case, surrounding spaces and ``_`` vs space.
    """

    def __init__(self, case_insensitive: bool = True) -> None:
        self.case_insensitive = case_insensitive

    # ---------------------------------------------------------------- #
    # Public API
    # ---------------------------------------------------------------- #

    def merge_positional(
        self,
        text: str,
        template_name: str,
        values: list[str],
        *,
        sort: bool = False,
    ) -> str:
        """Merge ``values`` into ``{{template_name|v1|v2|...}}``.

        Appends the template when missing, otherwise adds only the values
        that are not already present, keeping the existing order. Explicit
        numbered parameters (``1=ar``) are normalized to positional ones and
        named parameters are kept (after the positional ones).
        """
        clean = [v.strip() for v in values if v and v.strip()]
        if not clean:
            return text

        parsed = wtp.parse(text)
        tpl = self.find(parsed, template_name)

        if tpl is None:
            merged = self._dedupe(clean)
            if sort:
                merged.sort(key=self._key)
            new_tpl = self._render(template_name, merged, [])
            return f"{text}\n{new_tpl}" if text else new_tpl

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
        merged = self._dedupe(old + clean)
        if len(merged) == len(self._dedupe(old)):
            return text  # nothing new
        if sort:
            merged.sort(key=self._key)

        new_tpl = self._render(tpl.name.strip(), merged, named)
        return text.replace(tpl.string, new_tpl, 1)

    def add_unique(
        self,
        text: str,
        template_name: str,
        first_param_value: str,
    ) -> str:
        """Append ``{{template_name|1=value}}`` unless the same one exists."""
        new_tpl = f"{{{{{template_name}|1={first_param_value}}}}}"
        if not text:
            return new_tpl

        wanted = self._key(first_param_value)
        for t in wtp.parse(text).templates:
            if self.norm_name(t.name) != self.norm_name(template_name):
                continue
            arg = next((a for a in t.arguments if a.name.strip() == "1"), None)
            if arg and self._key(arg.value) == wanted:
                return text
        return f"{text}\n{new_tpl}"

    def ensure_named(
        self,
        text: str,
        template_name: str,
        param_name: str,
        default_value: str,
        *,
        position: Literal["start", "end"] = "start",
        replace: bool = False,
        dedupe: bool = True,
    ) -> str:
        """Ensure ``param_name`` exists in the template, at the requested place.

        Args:
            position: ``"start"`` puts the parameter before the positional
                values, ``"end"`` puts it after everything else.
            replace: If True, an existing value is overwritten with
                ``default_value``. If False, the last non-empty existing
                value is kept (``default_value`` is used only when the
                parameter is missing or empty).
            dedupe: Remove duplicated named parameters (the last non-empty
                value wins). The target parameter itself always appears once.

        The template is rebuilt in a fixed order, so whitespace/newlines
        between its parameters are not preserved. Returns ``text`` unchanged
        when the template is not found.
        """
        parsed = wtp.parse(text)
        tpl = self.find(parsed, template_name)
        if tpl is None:
            return text

        wanted = self.norm_name(param_name)
        positional: list[tuple[int, str]] = []
        others: dict[str, tuple[str, str]] = {}  # normalized name -> (name, value)
        others_list: list[tuple[str, str]] = []  # used when dedupe=False
        target_value = ""

        for a in tpl.arguments:
            name = a.name.strip()
            value = a.value.strip()
            if name.isdigit():
                if value:
                    positional.append((int(name), value))
                continue

            key = self.norm_name(name)
            if key == wanted:
                if value:
                    target_value = value  # the last non-empty value wins
                continue

            if dedupe:
                prev = others.get(key)
                if prev is None or value:
                    others[key] = (name, value or (prev[1] if prev else ""))
            else:
                others_list.append((name, value))

        if replace or not target_value:
            target_value = default_value

        pos_values = [v for _, v in sorted(positional)]
        other_named = [f"{n}={v}" for n, v in (others.values() if dedupe else others_list)]
        target = f"{param_name}={target_value}"

        if position == "start":
            parts = [target, *pos_values, *other_named]
        else:
            parts = [*pos_values, *other_named, target]

        new_tpl = "{{" + "|".join([tpl.name.strip(), *parts]) + "}}"
        return text.replace(tpl.string, new_tpl, 1)

    def delete_values(
        self,
        text: str,
        template_name: str,
        values: list[str],
        only_first: bool = True,
    ) -> str:
        """Remove every parameter of the template whose value is in ``values``."""
        unwanted = {self._key(v) for v in values if v}
        if not unwanted:
            return text

        parsed = wtp.parse(text)
        tpls = self.find_all(parsed, template_name)
        if not tpls:
            return text

        for tpl in tpls:
            for param in tpl.arguments:
                if param.value and self._key(param.value) in unwanted:
                    param.string = ""

            if only_first:
                break

        return parsed.string

    def remove_named(
        self,
        text: str,
        template_name: str,
        param_name: str,
    ) -> str:
        """Remove every occurrence of the named parameter from the template."""
        parsed = wtp.parse(text)
        tpl = self.find(parsed, template_name)
        if tpl is None:
            return text

        wanted = self.norm_name(param_name)
        for param in tpl.arguments:
            if self.norm_name(param.name) == wanted:
                param.string = ""

        return parsed.string

    # ---------------------------------------------------------------- #
    # Helpers
    # ---------------------------------------------------------------- #

    def find_all(self, parsed: wtp.WikiText, name: str) -> list[wtp.Template]:
        """Return all template called ``name``."""
        target = self.norm_name(name)
        return [t for t in parsed.templates if self.norm_name(t.name) == target]

    def find(self, parsed: wtp.WikiText, name: str) -> wtp.Template | None:
        """Return the first template called ``name`` (or None)."""
        temps = self.find_all(parsed, name)
        return temps[0] if temps else None

    @staticmethod
    def norm_name(name: str) -> str:
        """Normalize a template/parameter name for comparison."""
        return name.replace("_", " ").strip().lower()

    def _key(self, value: str) -> str:
        result = value.replace("_", " ").strip()
        return result.lower() if self.case_insensitive else result

    def _dedupe(self, values: list[str]) -> list[str]:
        seen: dict[str, str] = {}
        for v in values:
            seen.setdefault(self._key(v), v)
        return list(seen.values())

    @staticmethod
    def _render(name: str, positional: list[str], named: list[str]) -> str:
        return "{{" + "|".join([name, *positional, *named]) + "}}"

    @staticmethod
    def _get_argument(
        template: wtp.Template,
        params: list[str],
    ) -> wtp.Argument | None:
        """Return the first argument matching one of ``params`` (in order)."""
        norm = TemplateEditor.norm_name
        args_map = {norm(a.name): a for a in template.arguments}
        for param in params:
            found = args_map.get(norm(param))
            if found:
                return found
        return None


__all__ = [
    "TemplateEditor",
]
