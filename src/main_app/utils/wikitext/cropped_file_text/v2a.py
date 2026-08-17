"""Utilities for adding an ``other versions`` parameter to wikitext templates."""

from __future__ import annotations

import logging
from typing import Sequence

import wikitextparser as wtp

logger = logging.getLogger(__name__)

DEFAULT_MAIN_TEMPLATE_ARGS: tuple[str, ...] = ("other versions", "other_versions")


class OtherVersionsAdder:
    """Adds ``{{<temp_name>|1=<first_param_value>}}`` to a template's
    "other versions" parameter inside wikitext.

    Typical usage::

        adder = OtherVersionsAdder(
            temp_name="Extracted from",
            first_param_value="Original.svg",
        )
        new_text = adder.add(text)

    Args:
        temp_name: Name of the template to insert (e.g. ``"Extracted from"``).
        first_param_value: Value for the inserted template's first
            (unnamed / ``1=``) parameter.
        main_template_name: Name of the template whose parameter should be
            edited (defaults to ``"Information"``).
        main_template_args: Candidate parameter names to look for on the
            main template. The first name is used when creating a new
            parameter (defaults to ``("other versions", "other_versions")``).
        case_insensitive: Whether parameter value comparisons should be
            case-insensitive (defaults to ``True``).
    """

    def __init__(
        self,
        temp_name: str,
        first_param_value: str,
        main_template_name: str = "Information",
        main_template_args: Sequence[str] | None = None,
        case_insensitive: bool = True,
    ) -> None:
        self.temp_name = temp_name
        self.first_param_value = first_param_value
        self.main_template_name = main_template_name
        self.main_template_args = (
            list(main_template_args)
            if main_template_args is not None
            else list(DEFAULT_MAIN_TEMPLATE_ARGS)
        )
        self.case_insensitive = case_insensitive

    # ---------------------------------------------------------------- #
    # Public API
    # ---------------------------------------------------------------- #

    def add(self, text: str) -> str:
        """Add the configured template to the main template's parameter.

        Args:
            text: The wikitext content to modify.

        Returns:
            The modified wikitext, or the original text unchanged if the
            main template could not be found.
        """
        parsed = wtp.parse(text)
        target = self._find_main_template(parsed)

        if target is None:
            return text

        self._apply_to_template(target)
        return parsed.string

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

    def _apply_to_template(self, template: wtp.Template) -> None:
        """Update or create the "other versions" parameter on the given template."""
        existing_arg = self._get_named_arg(template, self.main_template_args)
        existing_value = (
            existing_arg.value.strip() if existing_arg and existing_arg.value else ""
        )

        new_value = self._merge_value(existing_value)

        if existing_arg:
            existing_arg.value = new_value
        else:
            # Prefer the first name from the configured list
            preferred_name = self.main_template_args[0]
            template.set_arg(preferred_name, new_value)

    def _merge_value(self, existing_value: str) -> str:
        """Return ``existing_value`` with the new template appended, avoiding duplicates."""
        insertion = self._render_insertion()

        if not existing_value:
            return insertion

        if self._already_present(existing_value, insertion):
            return existing_value

        return f"{existing_value.strip()}\n{insertion}"

    def _already_present(self, existing_value: str, insertion: str) -> bool:
        """Return True if the target template is already present."""
        # Exact text match
        if insertion in existing_value or existing_value.strip() == insertion.strip():
            return True

        # Semantic match (same template name + same first parameter value)
        current_first_param = self._get_template_param(
            existing_value, self.temp_name, ["1"]
        )
        if current_first_param is None:
            return False

        return self._normalize(current_first_param) == self._normalize(
            self.first_param_value
        )

    def _render_insertion(self) -> str:
        """Build the template string to insert."""
        return f"{{{{{self.temp_name}|1={self.first_param_value}}}}}"

    def _normalize(self, text: str) -> str:
        """Normalize text for comparison."""
        result = text.replace("_", " ").strip()
        return result.lower() if self.case_insensitive else result

    @staticmethod
    def _get_named_arg(
        template: wtp.Template, param_names: Sequence[str]
    ) -> wtp.Argument | None:
        """Return the first matching argument from ``param_names``."""
        args_by_name = {
            arg.name.lower().strip(): arg for arg in template.arguments
        }
        for param in param_names:
            found = args_by_name.get(param) or args_by_name.get(param.lower())
            if found:
                return found
        return None

    @classmethod
    def _get_template_param(
        cls, text: str, temp_name: str, param_names: Sequence[str]
    ) -> str | None:
        """Extract a parameter value from the first matching template in ``text``."""
        templates = wtp.WikiText(text).templates
        matches = [
            t for t in templates
            if str(t.normal_name()).strip() == temp_name.strip()
        ]
        if not matches:
            return None

        arg = cls._get_named_arg(matches[0], param_names)
        return str(arg.value).strip() if arg else None


def add_other_versions_new(
    *,
    text: str,
    temp_name: str,
    first_param_valve: str,  # kept for backward compatibility
    main_template_name: str = "Information",
    main_template_args: list[str] | None = None,
) -> str:
    """Backward-compatible function wrapper around :class:`OtherVersionsAdder`.

    Prefer using :class:`OtherVersionsAdder` directly in new code.
    """
    adder = OtherVersionsAdder(
        temp_name=temp_name,
        first_param_value=first_param_valve,
        main_template_name=main_template_name,
        main_template_args=main_template_args,
    )
    return adder.add(text)


__all__ = [
    "OtherVersionsAdder",
    "add_other_versions_new",
]
