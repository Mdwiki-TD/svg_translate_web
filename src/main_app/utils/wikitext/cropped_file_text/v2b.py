"""Utilities for adding an ``other versions`` parameter to wikitext templates."""

from __future__ import annotations

import logging
from typing import Optional

import wikitextparser as wtp

logger = logging.getLogger(__name__)


class OtherVersionsManager:
    """Adds ``{{<temp_name>|1=<first_param_value>}}`` to a template's
    "other versions" parameter inside wikitext.

    The manager holds general, reusable configuration (which main template
    to target, which parameter names count as "other versions", and whether
    value comparison is case-insensitive). The actual template name/value to
    insert are passed per call to :meth:`add`, so a single instance can be
    reused across many texts and many different templates.

    Typical usage::

        manager = OtherVersionsManager()
        new_text = manager.add(text, temp_name="Extracted from", first_param_value="Original.svg")

    Args:
        main_template_name: Name of the template whose parameter should be
            edited (defaults to "Information").
        main_template_args: Candidate parameter names to look for on the
            main template (defaults to ``("other versions", "other_versions")``).
        case_insensitive: Whether duplicate-value comparison ignores case
            (defaults to True).
    """

    DEFAULT_MAIN_TEMPLATE = "Information"
    DEFAULT_MAIN_ARGS: tuple[str, ...] = ("other versions", "other_versions")

    def __init__(
        self,
        main_template_name: str = DEFAULT_MAIN_TEMPLATE,
        main_template_args: Optional[list[str]] = None,
        case_insensitive: bool = True,
    ) -> None:
        self.main_template_name = main_template_name
        self.main_template_args = list(main_template_args) if main_template_args else list(self.DEFAULT_MAIN_ARGS)
        self.case_insensitive = case_insensitive

    # ---------------------------------------------------------------- #
    # Public API
    # ---------------------------------------------------------------- #

    def add(self, text: str, temp_name: str, first_param_value: str) -> str:
        """Add ``|other versions = {{temp_name|1=first_param_value}}`` to the
        main template (e.g. ``{{Information}}``).

        Args:
            text: The wikitext content to modify.
            temp_name: Name of the template to insert (e.g. "Extracted from").
            first_param_value: Value for the inserted template's first
                (unnamed / ``1=``) parameter.

        Returns:
            The modified wikitext, or the original text unchanged if the
            main template could not be found.
        """
        parsed = wtp.parse(text)
        template = self._find_main_template(parsed)

        if template is None:
            return text

        self._apply_to_template(template, temp_name, first_param_value)
        return parsed.string

    def get_template_param(self, text: str, template_name: str, params: list[str]) -> Optional[str]:
        """Extract the value of a specific parameter from a given template in the text."""
        matching = [
            t for t in wtp.WikiText(text).templates
            if str(t.normal_name()).strip() == template_name.strip()
        ]
        if not matching:
            return None

        arg = self._get_argument(matching[0], params)
        return str(arg.value).strip() if arg else None

    # ---------------------------------------------------------------- #
    # Internal helpers
    # ---------------------------------------------------------------- #

    def _find_main_template(self, parsed: wtp.WikiText) -> Optional[wtp.Template]:
        name = self.main_template_name.lower()
        for template in parsed.templates:
            if template.name.strip().lower() == name:
                return template
        return None

    def _apply_to_template(self, template: wtp.Template, temp_name: str, first_param_value: str) -> None:
        arg = self._get_argument(template, self.main_template_args)
        current_value = arg.value.strip() if arg and arg.value else ""

        new_value = self._merge_value(current_value, temp_name, first_param_value)

        if arg:
            arg.value = new_value
        else:
            preferred_name = self.main_template_args[0]
            template.set_arg(preferred_name, new_value)

    def _merge_value(self, current_value: str, temp_name: str, first_param_value: str) -> str:
        """Return ``current_value`` with the new template appended, avoiding duplicates."""
        insertion = self._build_new_template(temp_name, first_param_value)

        if not current_value:
            return insertion

        if self._is_duplicate(current_value, insertion, temp_name, first_param_value):
            return current_value

        return f"{current_value.strip()}\n{insertion}"

    def _is_duplicate(
        self,
        current_value: str,
        insertion: str,
        temp_name: str,
        first_param_value: str,
    ) -> bool:
        if insertion in current_value or current_value.strip() == insertion.strip():
            return True

        existing_param = self.get_template_param(current_value, temp_name, ["1"])
        if existing_param is None:
            return False

        return self._normalize(existing_param) == self._normalize(first_param_value)

    def _normalize(self, text: str) -> str:
        result = text.replace("_", " ").strip()
        return result.lower() if self.case_insensitive else result

    @staticmethod
    def _build_new_template(temp_name: str, first_param_value: str) -> str:
        return f"{{{{{temp_name}|1={first_param_value}}}}}"

    @staticmethod
    def _get_argument(template: wtp.Template, params: list[str]) -> Optional[wtp.Argument]:
        args_map = {arg.name.lower().strip(): arg for arg in template.arguments}
        for param in params:
            found = args_map.get(param) or args_map.get(param.lower())
            if found:
                return found
        return None


def add_other_versions_new(
    *,
    text: str,
    temp_name: str,
    first_param_valve: str,  # kept for backward compatibility
    main_template_name: str = "Information",
    main_template_args: list[str] | None = None,
) -> str:
    """Backward-compatible function wrapper around :class:`OtherVersionsManager`."""
    manager = OtherVersionsManager(
        main_template_name=main_template_name,
        main_template_args=main_template_args,
    )
    return manager.add(text, temp_name, first_param_valve)


__all__ = [
    "OtherVersionsManager",
    "add_other_versions_new",
]
