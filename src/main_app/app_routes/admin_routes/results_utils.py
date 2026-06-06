import logging
from typing import Any

logger = logging.getLogger(__name__)

FIX_BY_JOB_TYPE = {}


def fix_add_svglanguages_template(data: dict[str, Any]) -> dict[str, Any]:
    """
    { "pages_processed": [ { "steps": { "load_template_text": { "msg": "Skipped - page content is already has {{SVGLanguages|...}}" } } } ] }
    """
    if data.get("pages_skipped"):
        return data

    _pages_success = []
    _pages_failed = []
    _pages_skipped = []
    _pages_processed = []

    msg = "Skipped - page content is already has {{SVGLanguages|...}}"

    pages_processed = data.get("templates_processed") or data.get("pages_processed")
    for page in pages_processed:
        template_title = page.get("template_title") or page.get("title")

        if page.get("status") == "completed":
            _pages_success.append(page)
            continue

        if page.get("status") == "failed":
            _pages_failed.append(page)
            continue

        if page.get("steps", {}).get("load_template_text", {}).get("msg") == msg:
            _pages_skipped.append({"title": template_title, "msg": msg})
            continue

        _pages_processed.append(page)

    data["pages_skipped"] = _pages_skipped
    data["pages_processed"] = _pages_processed
    data["pages_failed"] = _pages_failed
    data["pages_success"] = _pages_success

    data["summary"] = data.get("summary", {})

    data["summary"].update(
        {
            "failed": len(_pages_failed),
            "skipped": len(_pages_skipped),
            "success": len(_pages_success),
        }
    )

    return data


def fix_result_data(result_data: dict[str, Any], job_type: str) -> dict[str, Any]:
    if not result_data:
        return result_data

    if job_type in FIX_BY_JOB_TYPE:
        try:
            return FIX_BY_JOB_TYPE[job_type](result_data)
        except Exception as e:
            logger.error(f"Error while fixing result data for job type {job_type}: {e}")
            return result_data

    return result_data


FIX_BY_JOB_TYPE = {
    "add_svglanguages_template": fix_add_svglanguages_template,
}
