

from pathlib import Path
import logging
import tempfile
from CopySVGTranslation import match_nested_tags, fix_nested_file  # type: ignore
from ...tasks.downloads import download_one_file
from ...tasks.uploads import upload_file

logger = logging.getLogger("svg_translate")


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

    if not user or not hasattr(user, "site"):
        return {
            "ok": False,
            "error": "unauthenticated",
        }

    logger.info(f"Uploading fixed file: {filename}")

    result = upload_file(
        file_name=filename,
        file_path=file_path,
        site=user.site,
        summary=f"Fixed {tags_fixed} nested tag(s) using svg_translate_web",
    )

    if not result:
        return {
            "ok": False,
            "error": "upload_failed",
        }

    return {
        "ok": True,
        "result": result,
    }


def process_fix_nested(filename: str, user) -> dict:
    """High-level orchestration for fixing nested SVG tags."""
    temp_dir = Path(tempfile.mkdtemp())

    download = download_svg_file(filename, temp_dir)
    if not download["ok"]:
        return {
            "success": False,
            "message": f"Failed to download file: {filename}",
            "details": download,
        }

    file_path = download["path"]

    detect_before = detect_nested_tags(file_path)
    if detect_before["count"] == 0:
        return {
            "success": False,
            "message": f"No nested tags found in {filename}",
            "details": {"nested_count": 0},
        }

    if not fix_nested_tags(file_path):
        return {
            "success": False,
            "message": f"Failed to fix nested tags in {filename}",
            "details": {"nested_count": detect_before["count"]},
        }

    verify = verify_fix(file_path, detect_before["count"])
    if verify["fixed"] == 0:
        return {
            "success": False,
            "message": f"No nested tags were fixed in {filename}",
            "details": verify,
        }

    message = f"{verify['fixed']} nested tag(s) Fixed."

    upload = upload_fixed_svg(filename, file_path, verify["fixed"], user)
    if not upload["ok"]:
        message += ", but upload failed"
        return {
            "success": False,
            "message": message,
            "details": {**verify, **upload},
        }
    message += f", Successfully fixed and uploaded {filename}"
    return {
        "success": True,
        "message": message,
        "details": {
            **verify,
            "upload_result": upload["result"],
        },
    }
