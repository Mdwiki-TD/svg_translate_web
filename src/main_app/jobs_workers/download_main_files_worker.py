"""
Worker module for downloading main files from remote source to local filesystem.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

from .. import template_service
from ..config import settings
from . import jobs_service

logger = logging.getLogger("svg_translate")


def download_file_from_commons(
    filename: str,
    output_dir: Path,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """
    Download a single file from Wikimedia Commons.

    Args:
        filename: The file name (e.g., "File:Example.svg")
        output_dir: Directory where the file should be saved
        session: Optional requests session to use

    Returns:
        dict with keys: success (bool), path (str|None), size_bytes (int|None), error (str|None)
    """
    result = {
        "success": False,
        "path": None,
        "size_bytes": None,
        "error": None,
    }

    if not filename:
        result["error"] = "Empty filename"
        return result

    # Extract just the filename part (remove "File:" prefix if present)
    clean_filename = filename
    if clean_filename.startswith("File:"):
        clean_filename = clean_filename[5:]

    # Build the download URL using Special:FilePath
    url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{quote(clean_filename.replace(' ', '_'))}"

    # Determine output path - maintain original filename
    out_path = output_dir / clean_filename

    # Create session if not provided
    if session is None:
        session = requests.Session()
        session.headers.update({
            "User-Agent": settings.oauth.user_agent if settings.oauth else "SVGTranslateBot/1.0",
        })

    try:
        response = session.get(url, timeout=60, allow_redirects=True)
        response.raise_for_status()

        # Save the file
        out_path.write_bytes(response.content)
        file_size = len(response.content)

        result["success"] = True
        result["path"] = str(out_path)
        result["size_bytes"] = file_size
        logger.info(f"Downloaded: {clean_filename} ({file_size} bytes)")

    except requests.RequestException as e:
        result["error"] = f"Download failed: {str(e)}"
        logger.error(f"Failed to download {clean_filename}: {e}")
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
        logger.exception(f"Error saving {clean_filename}")

    return result


def process_downloads(
    job_id: int,
    result: dict[str, Any],
    result_file: str,
    output_dir: Path,
    cancel_event: threading.Event | None = None,
) -> dict[str, Any]:
    """
    Process downloading all main files for templates.

    Args:
        job_id: The job ID
        result: The result dictionary to populate
        result_file: The result file name
        output_dir: Directory to save downloaded files
        cancel_event: Optional event to check for cancellation

    Returns:
        The populated result dictionary
    """
    # Update job status to running
    try:
        jobs_service.update_job_status(job_id, "running", result_file, job_type="download_main_files")
    except LookupError:
        logger.warning(f"Job {job_id}: Could not update status to running, job record might have been deleted.")
        return result

    # Get all templates with main files
    templates = template_service.list_templates()
    templates_with_files = [t for t in templates if t.main_file]

    result["summary"]["total"] = len(templates_with_files)
    result["output_path"] = str(output_dir)

    logger.info(f"Job {job_id}: Found {len(templates_with_files)} templates with main files")

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create a shared session for all downloads
    session = requests.Session()
    session.headers.update({
        "User-Agent": settings.oauth.user_agent if settings.oauth else "SVGTranslateBot/1.0",
    })

    for n, template in enumerate(templates_with_files, start=1):
        # Check for cancellation
        if cancel_event and cancel_event.is_set():
            logger.info(f"Job {job_id}: Cancellation detected, stopping.")
            result["status"] = "cancelled"
            result["cancelled_at"] = datetime.now().isoformat()
            break

        # Save progress periodically
        if n == 1 or n % 10 == 0:
            jobs_service.save_job_result_by_name(result_file, result)

        logger.info(f"Job {job_id}: Processing {n}/{len(templates_with_files)}: {template.title}")

        file_info = {
            "template_id": template.id,
            "template_title": template.title,
            "filename": template.main_file,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Check if file already exists locally
            clean_filename = template.main_file
            if clean_filename.startswith("File:"):
                clean_filename = clean_filename[5:]
            local_path = output_dir / clean_filename

            if local_path.exists():
                file_info["status"] = "already_local"
                file_info["path"] = str(local_path)
                file_info["size_bytes"] = local_path.stat().st_size
                result["files_already_local"].append(file_info)
                result["summary"]["already_local"] += 1
                logger.info(f"Job {job_id}: File already exists locally: {clean_filename}")
                continue

            # Download the file
            download_result = download_file_from_commons(
                template.main_file,
                output_dir,
                session=session,
            )

            if download_result["success"]:
                file_info["status"] = "downloaded"
                file_info["path"] = download_result["path"]
                file_info["size_bytes"] = download_result["size_bytes"]
                result["files_downloaded"].append(file_info)
                result["summary"]["downloaded"] += 1
            else:
                file_info["status"] = "failed"
                file_info["reason"] = download_result["error"]
                result["files_failed"].append(file_info)
                result["summary"]["failed"] += 1
                logger.warning(f"Job {job_id}: Failed to download {template.main_file}: {download_result['error']}")

        except Exception as e:
            file_info["status"] = "failed"
            file_info["reason"] = f"Exception: {str(e)}"
            file_info["error_type"] = type(e).__name__
            result["files_failed"].append(file_info)
            result["summary"]["failed"] += 1
            logger.exception(f"Job {job_id}: Error processing {template.title}")

    # Final save
    result["completed_at"] = datetime.now().isoformat()
    jobs_service.save_job_result_by_name(result_file, result)

    # Update job status
    final_status = "completed"
    if result.get("status") == "cancelled":
        final_status = "cancelled"

    try:
        jobs_service.update_job_status(job_id, final_status, result_file, job_type="download_main_files")
    except LookupError:
        logger.warning(f"Job {job_id}: Could not update status to {final_status}, job record might have been deleted.")

    logger.info(
        f"Job {job_id} {final_status}: "
        f"{result['summary']['downloaded']} downloaded, "
        f"{result['summary']['failed']} failed, "
        f"{result['summary']['already_local']} already local"
    )

    return result


def download_main_files_for_templates(
    job_id: int,
    user: Any | None = None,
    cancel_event: threading.Event | None = None,
) -> None:
    """
    Background worker to download main files for all templates.

    This function:
    1. Fetches all templates from the database
    2. For each template with a main_file:
       - Downloads the file from Commons
       - Saves it to settings.paths.main_files_path
    3. Saves a detailed report to a JSON file

    Args:
        job_id: The job ID
        user: User authentication data (not used for downloads, but kept for consistency)
        cancel_event: Optional event to check for cancellation
    """
    logger.info(f"Starting job {job_id}: download main files for templates")
    job_type = "download_main_files"

    # Get output directory from settings
    output_dir = Path(settings.paths.main_files_path)

    # Initialize result tracking
    result = {
        "job_id": job_id,
        "started_at": datetime.now().isoformat(),
        "output_path": str(output_dir),
        "files_downloaded": [],
        "files_failed": [],
        "files_skipped": [],
        "files_already_local": [],
        "summary": {
            "total": 0,
            "downloaded": 0,
            "failed": 0,
            "skipped": 0,
            "already_local": 0,
        },
    }

    result_file = jobs_service.generate_result_file_name(job_id, job_type)

    try:
        result = process_downloads(
            job_id,
            result,
            result_file,
            output_dir,
            cancel_event=cancel_event,
        )
    except Exception as e:
        logger.exception(f"Job {job_id}: Fatal error during execution")

        # Save error result
        error_result = {
            "job_id": job_id,
            "started_at": result.get("started_at", datetime.now().isoformat()),
            "completed_at": datetime.now().isoformat(),
            "output_path": str(output_dir),
            "error": str(e),
            "error_type": type(e).__name__,
        }

        try:
            jobs_service.save_job_result_by_name(result_file, error_result)
            jobs_service.update_job_status(job_id, "failed", result_file, job_type="download_main_files")
        except LookupError:
            logger.warning(f"Job {job_id}: Could not update status to failed, job record might have been deleted.")
        except Exception:
            logger.exception(f"Job {job_id}: Failed to save error result")
            try:
                jobs_service.update_job_status(job_id, "failed", job_type="download_main_files")
            except LookupError:
                pass


__all__ = [
    "download_main_files_for_templates",
]
