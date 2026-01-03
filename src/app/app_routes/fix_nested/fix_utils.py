

from pathlib import Path
import logging
import tempfile
import json
import shutil
from datetime import datetime
from typing import Optional
from CopySVGTranslation import match_nested_tags, fix_nested_file  # type: ignore
from ...tasks.downloads import download_one_file
from ...tasks.uploads import upload_file, get_user_site
from ...config import settings
from ...db.fix_nested_task_store import FixNestedTaskStore
# from ...db.db_class import Database
from werkzeug.utils import secure_filename
logger = logging.getLogger("svg_translate")


def create_task_folder(task_id: str) -> Path:
    """Create folder structure for a fix_nested task."""
    task_dir = Path(settings.paths.fix_nested_data) / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    return task_dir


def save_metadata(task_dir: Path, metadata: dict) -> None:
    """Save task metadata to JSON file."""
    metadata_file = task_dir / "metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, default=str)


def log_to_task(task_dir: Path, message: str) -> None:
    """Append log message to task log file."""
    log_file = task_dir / "task_log.txt"
    timestamp = datetime.now().isoformat()
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


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

    if not result.get("result") == "Success":
        return {
            "ok": False,
            "error": result.get("error", "upload_failed"),
        }

    return {
        "ok": True,
        "result": result,
    }


def process_fix_nested(
    filename: str,
    user,
    task_id: Optional[str] = None,
    username: Optional[str] = None,
    db_store: Optional[FixNestedTaskStore] = None
) -> dict:
    """High-level orchestration for fixing nested SVG tags.

    Args:
        filename: Name of the SVG file to fix
        user: User authentication data
        task_id: Optional task ID for saving files to persistent storage
        username: Username of the user
        db_store: Optional database store for task management
    """
    # Use temp directory for processing
    temp_dir = Path(tempfile.mkdtemp())

    # Create task folder if task_id is provided
    task_dir = None
    if task_id:
        task_dir = create_task_folder(task_id)
        log_to_task(task_dir, f"Starting fix_nested task for file: {filename}")

        # Create database record if store is provided
        if db_store:
            db_store.create_task(task_id, filename, username)
            db_store.update_status(task_id, "running")

    # Prepare metadata
    metadata = {
        "task_id": task_id,
        "filename": filename,
        "username": username,
        "started_at": datetime.now().isoformat(),
        "status": "running",
    }

    download = download_svg_file(filename, temp_dir)
    if not download["ok"]:
        if task_dir:
            log_to_task(task_dir, f"Download failed: {download.get('error')}")
            metadata["status"] = "failed"
            metadata["error"] = "download_failed"
            metadata["download_result"] = download
            save_metadata(task_dir, metadata)
        if db_store and task_id:
            db_store.update_error(task_id, "download_failed")
            db_store.update_download_result(task_id, download)
        return {
            "success": False,
            "message": f"Failed to download file: {filename}",
            "details": download,
        }

    file_path = download["path"]

    # Save original file if task_dir exists
    if task_dir:
        original_file = task_dir / "original.svg"
        shutil.copy2(file_path, original_file)
        log_to_task(task_dir, f"Original file saved to: {original_file}")
        metadata["download_result"] = {"status": "success", "path": str(original_file)}
        if db_store and task_id:
            db_store.update_download_result(task_id, {"status": "success", "path": str(original_file)})

    detect_before = detect_nested_tags(file_path)
    if task_dir:
        log_to_task(task_dir, f"Nested tags detected: {detect_before['count']}")
        metadata["nested_tags_before"] = detect_before["count"]
    if db_store and task_id:
        db_store.update_nested_counts(task_id, before=detect_before["count"])

    if detect_before["count"] == 0:
        if task_dir:
            log_to_task(task_dir, "No nested tags found")
            metadata["status"] = "completed"
            metadata["nested_tags_after"] = 0
            metadata["nested_tags_fixed"] = 0
            save_metadata(task_dir, metadata)
        if db_store and task_id:
            db_store.update_nested_counts(task_id, after=0, fixed=0)
            db_store.update_status(task_id, "completed")
        return {
            "success": False,
            "message": f"No nested tags found in {filename}",
            "details": {"nested_count": 0},
        }

    if not fix_nested_tags(file_path):
        if task_dir:
            log_to_task(task_dir, "Failed to fix nested tags")
            metadata["status"] = "failed"
            metadata["error"] = "fix_failed"
            save_metadata(task_dir, metadata)
        if db_store and task_id:
            db_store.update_error(task_id, "fix_failed")
        return {
            "success": False,
            "message": f"Failed to fix nested tags in {filename}",
            "details": {"nested_count": detect_before["count"]},
        }

    verify = verify_fix(file_path, detect_before["count"])
    if task_dir:
        log_to_task(task_dir, f"Fixed tags: {verify['fixed']}, remaining: {verify['after']}")
        metadata["nested_tags_after"] = verify["after"]
        metadata["nested_tags_fixed"] = verify["fixed"]
    if db_store and task_id:
        db_store.update_nested_counts(task_id, after=verify["after"], fixed=verify["fixed"])

    if verify["fixed"] == 0:
        if task_dir:
            log_to_task(task_dir, "No tags were fixed")
            metadata["status"] = "failed"
            metadata["error"] = "no_tags_fixed"
            save_metadata(task_dir, metadata)
        if db_store and task_id:
            db_store.update_error(task_id, "no_tags_fixed")
        return {
            "success": False,
            "message": f"No nested tags were fixed in {filename}",
            "details": verify,
        }

    # Save fixed file if task_dir exists
    if task_dir:
        fixed_file = task_dir / "fixed.svg"
        shutil.copy2(file_path, fixed_file)
        log_to_task(task_dir, f"Fixed file saved to: {fixed_file}")

    upload = upload_fixed_svg(filename, file_path, verify["fixed"], user)
    if task_dir:
        if upload["ok"]:
            log_to_task(task_dir, f"Upload successful: {upload.get('result')}")
            metadata["upload_result"] = upload["result"]
            metadata["status"] = "completed"
        else:
            log_to_task(task_dir, f"Upload failed: {upload.get('error')}")
            metadata["upload_result"] = {"error": upload.get("error")}
            metadata["status"] = "upload_failed"
        metadata["completed_at"] = datetime.now().isoformat()
        save_metadata(task_dir, metadata)

    if db_store and task_id:
        if upload["ok"]:
            db_store.update_upload_result(task_id, upload["result"])
            db_store.update_status(task_id, "completed")
        else:
            db_store.update_upload_result(task_id, {"error": upload.get("error")})
            db_store.update_status(task_id, "upload_failed")

    if not upload["ok"]:
        return {
            "success": False,
            "message": f"Fixed {verify['fixed']} nested tag(s), but upload failed.",
            "details": {**verify, **upload},
        }

    return {
        "success": True,
        "message": f"Successfully fixed {verify['fixed']} nested tag(s) and uploaded {filename}.",
        "details": {
            **verify,
            "upload_result": upload["result"],
            "task_id": task_id,
        },
    }


def process_fix_nested_file_simple(
    file,
) -> dict:
    """High-level orchestration for fixing nested SVG tags.

    Args:
        file: The SVG file to fix
    """
    # Use temp directory for processing
    temp_dir = Path(tempfile.mkdtemp())

    # Sanitize filename to prevent path traversal
    safe_filename = secure_filename(file.filename or "upload.svg")
    file_path = temp_dir / safe_filename

    try:
        file.save(file_path)
    except Exception as e:
        # Clean up on error
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        return {
            "success": False,
            "message": "Failed to save uploaded file.",
            "details": {"error": str(e)},
        }

    metadata = {
        "nested_tags_before": 0,
        "nested_tags_fixed": 0,
        "nested_tags_after": 0,
    }

    detect_before = detect_nested_tags(file_path)
    metadata["nested_tags_before"] = detect_before["count"]

    if detect_before["count"] == 0:
        return {
            "success": False,
            "message": "No nested tags found in the uploaded file.",
            "details": {"nested_count": 0},
        }

    if not fix_nested_tags(file_path):
        return {
            "success": False,
            "message": "Failed to fix nested tags in the uploaded file.",
            "details": {"nested_count": detect_before["count"]},
        }

    verify = verify_fix(file_path, detect_before["count"])

    if verify["fixed"] == 0:
        return {
            "success": False,
            "message": "No nested tags were fixed in the uploaded file.",
            "details": verify,
        }

    return {
        "success": True,
        "message": f"Successfully fixed {verify['fixed']} nested tag(s)",
        "details": verify,
        "file_path": file_path,
    }
