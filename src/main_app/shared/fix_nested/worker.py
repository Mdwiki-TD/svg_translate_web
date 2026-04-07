import logging
from pathlib import Path

from CopySVGTranslation import fix_nested_file, match_nested_tags  # type: ignore

from ...api_services.clients import get_user_site
from ...api_services.upload_bot import upload_file
from ...api_services.utils import download_one_file

logger = logging.getLogger(__name__)


def download_svg_file(filename: str, temp_dir: Path) -> dict:
    """Download SVG file and return file path or error info."""
    logger.info(f"Downloading file: {filename}")

    file_data = download_one_file(
        title=filename,
        out_dir=temp_dir,
        i=1,
        overwrite=True,
    )

    if file_data.get("result") != "success":
        return {
            "ok": False,
            "error": "download_failed",
            "details": file_data,
        }

    return {
        "ok": True,
        "path": Path(file_data["path"]),
    }


def detect_nested_tags(file_path: Path) -> dict:
    """Detect nested tags in SVG file."""
    nested = match_nested_tags(str(file_path))
    return {
        "count": len(nested),
        "tags": nested,
    }


def fix_nested_tags(file_path: Path) -> bool:
    """Fix nested tags in-place."""
    logger.info(f"Fixing nested tags in: {file_path.name}")
    return bool(fix_nested_file(file_path, file_path))


def verify_fix(file_path: Path, before_count: int) -> dict:
    """Verify nested tags count after fix."""
    after = match_nested_tags(str(file_path))
    after_count = len(after)

    return {
        "before": before_count,
        "after": after_count,
        "fixed": max(0, before_count - after_count),
    }


def upload_fixed_svg(
    filename: str,
    file_path: Path,
    tags_fixed: int,
    user,
) -> dict:
    """Upload fixed SVG file to Commons."""
    if not user:
        return {
            "ok": False,
            "error": "unauthenticated",
        }

    site = get_user_site(user)

    if not site:
        return {
            "ok": False,
            "error": "oauth-auth-failed",
        }

    logger.info(f"Uploading fixed file: {filename}")

    result = upload_file(
        file_name=filename,
        file_path=file_path,
        site=site,
        summary=f"Fixed {tags_fixed} nested tag(s) using svg_translate_web",
    )

    if result.get("result") != "Success":
        return {
            "ok": False,
            "error": result.get("error", "upload_failed"),
            "error_details": result.get("error_details", ""),
        }

    return {
        "ok": True,
        "result": result,
    }
