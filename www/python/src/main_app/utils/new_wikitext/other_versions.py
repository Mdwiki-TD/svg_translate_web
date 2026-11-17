"""Utilities for adding/updating templates inside the ``other versions``
parameter of a main template (e.g. ``{{Information}}``) in wikitext."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Literal

import wikitextparser as wtp

from ...parsers.template_editor import TemplateEditor

logger = logging.getLogger(__name__)

SVG_LANG_TEMPLATE = "Svg lang"


class OtherVersionsUpdater:
    """Applies :class:`TemplateEditor` operations to the "other versions" parameter.

    This class only knows *where* to work: it finds the parameter of the main
    template, hands its value to the editor, and writes the result back
    (creating the parameter when needed). All template-level logic lives in
    :class:`TemplateEditor`, which can be reused for any other template.

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
        editor: Custom editor instance (a default one is created from
            ``case_insensitive`` when omitted).
    """

    DEFAULT_MAIN_TEMPLATE = "Information"
    DEFAULT_PARAM_NAMES: tuple[str, ...] = ("other versions", "other_versions")

    def __init__(
        self,
        main_template_name: str = DEFAULT_MAIN_TEMPLATE,
        param_names: list[str] | None = None,
        case_insensitive: bool = True,
        editor: TemplateEditor | None = None,
    ) -> None:
        self.main_template_name = main_template_name
        self.param_names = list(param_names) if param_names else list(self.DEFAULT_PARAM_NAMES)
        self.case_insensitive = case_insensitive
        self.editor = editor or TemplateEditor(case_insensitive=case_insensitive)

    # ---------------------------------------------------------------- #
    # Generic operations (any template inside "other versions")
    # ---------------------------------------------------------------- #

    def merge_values(
        self,
        text: str,
        template_name: str,
        values: list[str],
        *,
        sort: bool = False,
    ) -> str:
        """Merge ``values`` into ``{{template_name|v1|v2|...}}``."""
        return self._update(
            text,
            lambda cur: self.editor.merge_positional(cur, template_name, values, sort=sort),
        )

    def add_template(
        self,
        text: str,
        template_name: str,
        first_param_value: str,
    ) -> str:
        """Append ``{{template_name|1=first_param_value}}`` unless already present."""
        return self._update(
            text,
            lambda cur: self.editor.add_unique(
                cur,
                template_name,
                first_param_value,
            ),
        )

    def ensure_named_param(
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
        """Ensure a named parameter exists in the template (see :meth:`TemplateEditor.ensure_named`)."""
        return self._update(
            text,
            lambda cur: self.editor.ensure_named(
                cur,
                template_name,
                param_name,
                default_value,
                position=position,
                replace=replace,
                dedupe=dedupe,
            ),
        )

    def remove_named_param(
        self,
        text: str,
        template_name: str,
        param_name: str,
    ) -> str:
        """Remove a named parameter from the template."""
        return self._update(
            text,
            lambda cur: self.editor.remove_named(cur, template_name, param_name),
        )

    # ---------------------------------------------------------------- #
    # Core: locate the parameter, apply the transform, write back
    # ---------------------------------------------------------------- #

    def _update(
        self,
        text: str,
        transform: Callable[[str], str],
    ) -> str:
        parsed = wtp.parse(text)

        main = self.editor.find(parsed, self.main_template_name)
        if main is None:
            logger.debug("Main template %r not found", self.main_template_name)
            return text

        arg = self.editor._get_argument(main, self.param_names)
        raw = arg.value if arg else ""
        current = raw.strip()

        new_value = transform(current)
        if new_value == current:
            return text

        if arg:
            trail = raw[len(raw.rstrip()) :]
            if current:
                lead = raw[: len(raw) - len(raw.lstrip())]
                arg.value = f"{lead}{new_value}{trail}"
            else:
                # Empty parameter: keep the original line break before the next param / closing braces.
                arg.value = f"{new_value}{trail}"
        else:
            main.set_arg(self.param_names[0], new_value)

        return parsed.string

    # ---- presets (add more here for other templates) ---------------- #

    def add_svg_langs(
        self,
        text: str,
        langs: list[str],
        *,
        sort: bool = False,
        values_to_delete: list[str] | None = None,
        dl_position: Literal["start", "end"] = "start",
        replace_dl: bool = False,
        dedupe_named: bool = True,
    ) -> str:
        """Add language codes to ``{{Svg lang|...}}`` and ensure ``dl=en`` is present."""
        filtered_langs = [lang.lower() for lang in langs if lang]

        if values_to_delete:
            values_to_delete = [x.lower() for x in values_to_delete if x]
            text = self.editor.delete_values(text, SVG_LANG_TEMPLATE, values_to_delete)
            filtered_langs = [lang for lang in filtered_langs if lang not in values_to_delete]

        if filtered_langs:
            text = self.merge_values(text, SVG_LANG_TEMPLATE, filtered_langs, sort=sort)

        return self.ensure_named_param(
            text,
            SVG_LANG_TEMPLATE,
            "dl",
            "en",
            position=dl_position,
            replace=replace_dl,
            dedupe=dedupe_named,
        )


__all__ = [
    "OtherVersionsUpdater",
]
