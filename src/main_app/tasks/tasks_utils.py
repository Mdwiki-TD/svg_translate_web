import html
import json
import logging
from urllib.parse import quote

logger = logging.getLogger("svg_translate")


def json_save(path, data):
    """
    Save Python data to a file as pretty-printed UTF-8 JSON.

    If `data` is None or empty, the function logs an error and returns without writing. Errors encountered while opening or writing the file are logged and not propagated.

    Parameters:
        path (str | os.PathLike): Destination file path where JSON will be written.
        data: JSON-serializable Python object to persist (e.g., dict, list).
    """
    logger.debug(f"Saving json to: {path}")

    if not data:
        logger.error(f"Empty data to save to: {path}")
        return
    # ---
    try:
        # p = Path(path)
        # p.parent.mkdir(parents=True, exist_ok=True)
        # with p.open("w", encoding="utf-8") as f:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    except (OSError, TypeError, ValueError) as e:
        logger.error(f"Error saving json: {e}, path: {str(path)}")
    except Exception:
        logger.exception(f"Unexpected error saving json, path: {str(path)}")


def commons_link(title, name=None):
    """Return an HTML anchor pointing to a Commons file page.

    Parameters:
        title (str): Page title used to build the Commons URL.
        name (str | None): Optional link text; falls back to ``title`` when None.

    Returns:
        str: HTML anchor tag safe for embedding in status messages.
    """
    safe_name = html.escape(name or title, quote=True)
    href = f"https://commons.wikimedia.org/wiki/{quote(title, safe='/:()')}"
    return f"<a href='{href}' target='_blank' rel='noopener noreferrer'>{safe_name}</a>"


def save_files_stats(data, output_dir):
    """Persist workflow statistics to ``files_stats.json`` within output_dir.

    Parameters:
        data (dict): Serializable summary data to write.
        output_dir (pathlib.Path): Directory that will receive the JSON file.
    """

    files_stats_path = output_dir / "files_stats.json"
    json_save(files_stats_path, data)

    logger.debug(f"files_stats at: {files_stats_path}")


def make_results_summary(
    len_files, files_to_upload_count, no_file_path, injects_result, translations, main_title, upload_result
):
    """Compile the final task result payload consumed by the UI and API.

    Parameters:
        len_files (int): Total number of files processed during the workflow.
        files_to_upload_count (int): Number of files with paths suitable for
            upload.
        no_file_path (int): Count of files lacking translated output paths.
        injects_result (dict): Aggregated statistics from the injection phase.
        translations (dict): Translation data summary used for injection.
        main_title (str): The primary Commons title associated with the task.
        upload_result (dict): Outcome of the upload stage.

    Returns:
        dict: Summary dictionary persisted to the database for task results.
    """
    return {
        "total_files": len_files,
        "files_to_upload_count": files_to_upload_count,
        "no_file_path": no_file_path,
        "injects_result": {
            "nested_files": injects_result.get("nested_files", 0),
            "success": injects_result.get("success", 0),
            "failed": injects_result.get("failed", 0),
        },
        "new_translations_count": len(translations.get("new", {})),
        "upload_result": upload_result,
        "main_title": main_title,
    }
