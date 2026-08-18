"""Utilities for adding an ``other versions`` parameter to wikitext templates."""

from __future__ import annotations

import logging

import wikitextparser as wtp

logger = logging.getLogger(__name__)


class OtherVersionsAdder:
    """Adds ``{{<temp_name>|1=<first_param_value>}}`` to a template's
    "other versions" parameter inside wikitext.

    The manager holds general, reusable configuration (which main template
    to target, which parameter names count as "other versions", and whether
    value comparison is case-insensitive). The actual template name/value to
    insert are passed per call to :meth:`add`, so a single instance can be
    reused across many texts and many different templates.

    Typical usage::

        adder = OtherVersionsAdder()
        new_text = adder.add(text, temp_name="Extracted from", first_param_value="Original.svg")

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
        main_template_args: list[str] | None = None,
        case_insensitive: bool = True,
    ) -> None:
        self.main_template_name = main_template_name
        self.main_template_args = (
            list(main_template_args) if main_template_args is not None else list(self.DEFAULT_MAIN_ARGS)
        )
        self.case_insensitive = case_insensitive

    # ---------------------------------------------------------------- #
    # Public API
    # ---------------------------------------------------------------- #

    def add(
        self,
        text: str,
        temp_name: str,
        first_param_value: str,
    ) -> str:
        """
        Add the configured template to the main template's parameter.

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
        target = self._find_main_template(parsed)

        if target is None:
            return text

        self._apply_to_template(target, temp_name, first_param_value)
        return parsed.string

    def get_template_param(self, text: str, template_name: str, params: list[str]) -> str | None:
        """
        Extract the value of a specific parameter from a given template in the text.
        """
        templates = wtp.WikiText(text).templates
        matches = [t for t in templates if str(t.normal_name()).strip() == template_name.strip()]
        if not matches:
            return None

        arg = self._get_argument(matches[0], params)
        return str(arg.value).strip() if arg else None

    # ---------------------------------------------------------------- #
    # Internal helpers
    # ---------------------------------------------------------------- #

    def _find_main_template(self, parsed: wtp.WikiText) -> wtp.Template | None:
        """Return the first template matching ``main_template_name``."""
        name = self.main_template_name.lower()
        for template in parsed.templates:
            if template.name.strip().lower() == name:
                return template
        return None

    def _apply_to_template(self, template: wtp.Template, temp_name: str, first_param_value: str) -> None:
        """Update or create the "other versions" parameter on the given template."""
        existing_arg = self._get_argument(template, self.main_template_args)
        current_value = existing_arg.value.strip() if existing_arg and existing_arg.value else ""

        new_value = self._merge_value(current_value, temp_name, first_param_value)

        if existing_arg:
            existing_arg.value = new_value
        else:
            # Prefer the first name from the configured list
            preferred_name = self.main_template_args[0]
            template.set_arg(preferred_name, new_value)

    def _merge_value(self, current_value: str, temp_name: str, first_param_value: str) -> str:
        """Return ``current_value`` with the new template appended, avoiding duplicates."""
        insertion = self._build_new_template(temp_name, first_param_value)

        if not current_value:
            return insertion

        if self._already_present(current_value, insertion, temp_name, first_param_value):
            return current_value

        return f"{current_value.strip()}\n{insertion}"

    def _already_present(
        self,
        current_value: str,
        insertion: str,
        temp_name: str,
        first_param_value: str,
    ) -> bool:
        """Return True if the target template is already present."""
        # Exact text match
        if insertion in current_value or current_value.strip() == insertion.strip():
            return True

        # Semantic match (same template name + same first parameter value)
        current_first_param = self.get_template_param(current_value, temp_name, ["1"])
        if current_first_param is None:
            return False

        return self._normalize(current_first_param) == self._normalize(first_param_value)

    def _normalize(self, text: str) -> str:
        """Normalize text for comparison."""
        result = text.replace("_", " ").strip()
        return result.lower() if self.case_insensitive else result

    @staticmethod
    def _build_new_template(temp_name: str, first_param_value: str) -> str:
        return f"{{{{{temp_name}|1={first_param_value}}}}}"

    @staticmethod
    def _get_argument(template: wtp.Template, params: list[str]) -> wtp.Argument | None:
        """Return the first matching argument from ``param_names``."""
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
    """
    Backward-compatible function wrapper around :class:`OtherVersionsAdder`.
    """
    adder = OtherVersionsAdder(
        main_template_name=main_template_name,
        main_template_args=main_template_args,
    )
    return adder.add(text, temp_name, first_param_valve)


__all__ = [
    "OtherVersionsAdder",
    "add_other_versions_new",
]
