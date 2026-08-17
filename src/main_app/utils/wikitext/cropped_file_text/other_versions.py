""" """

from __future__ import annotations

import logging

import wikitextparser as wtp

logger = logging.getLogger(__name__)


def _normalize_text(text: str, case_insensitive: bool = False) -> str:
    result = text.replace("_", " ").strip()
    return result.lower() if case_insensitive else result


def _get_args(template: wtp.Template, params: list[str]) -> wtp.Argument | None:
    tmp_args = {x.name.lower().strip(): x for x in template.arguments}
    for arg in params:
        arg_in = tmp_args.get(arg) or tmp_args.get(arg.lower())
        if arg_in:
            return arg_in

    return None


def get_temp_param(text: str, temp_name: str, params: list[str]) -> str | None:
    templates = wtp.WikiText(text).templates
    temp = [x for x in templates if str(x.normal_name()).strip() == temp_name.strip()]
    if temp:
        arg = _get_args(temp[0], params)
        if arg:
            return str(arg.value).strip()
    return None


def _add_it(args_in_value: str, temp_name: str, first_param_valve: str) -> str:
    text_to_add = f"{{{{{temp_name}|1={first_param_valve}}}}}"
    if not args_in_value:
        return text_to_add

    # NOTE: nothing to do here, to solve test_not_adding_duplicate_value
    #   analyze args_in_value if its contains <text_to_add> or they are equal
    if text_to_add in args_in_value or args_in_value.strip() == text_to_add.strip():
        return args_in_value

    # NOTE: solved test_other_versions.py::TestAddOtherVersionsNew::test_basic_not_duplicate
    #   fix duplicate insert when <args_in_value> include `{{ <temp_name> | <first_param_valve> }}`
    #   And we need to add `{{<Temp_name>|1=<first_param_valve>}}`
    new_temp = f"{args_in_value.strip()}\n{text_to_add}"

    args_in_first_param = get_temp_param(
        text=args_in_value,
        temp_name=temp_name,
        params=["1"],
    )

    # first check if <args_in_value> has template with name == <temp_name>
    if not args_in_first_param:
        return new_temp

    # search for <first_param_valve> in <args_in_first_param>
    if _normalize_text(args_in_first_param, True) == _normalize_text(first_param_valve, True):
        return args_in_value

    return new_temp


def add_other_versions_new(
    *,
    text: str,
    temp_name: str,
    first_param_valve: str,
    main_template_name: str = "Information",
    main_template_args: list[str] | None = None,
) -> str:
    """
    Add |other versions = {{<temp_name>|1=<first_param_valve>}} parameter to the {{Information}} template in wikitext.

    Args:
        text: The wikitext content to modify
        temp_name: The name of the template to add the parameter to
        first_param_valve: The value of the first parameter of the template

    Returns:
        The modified wikitext with the other versions parameter added

    TODO: if text include `{{Extracted from| Original.svg }}` and we need to add `{{Extracted from|1=Original.svg}}`
    """
    if not main_template_args:
        main_template_args = ["other versions", "other_versions"]

    parsed = wtp.parse(text)
    add_done = False

    for template in parsed.templates:
        if template.name.strip().lower() == main_template_name.lower():
            args_in = _get_args(template, main_template_args)
            args_in_value = args_in.value.strip() if args_in and args_in.value else ""

            formatted_new_value = _add_it(args_in_value, temp_name, first_param_valve)

            if args_in:
                args_in.value = formatted_new_value
                add_done = True
            else:
                template.set_arg("other versions", formatted_new_value)
                add_done = True
            break

    if not add_done:
        return text

    return parsed.string


__all__ = [
    "add_other_versions_new",
]
