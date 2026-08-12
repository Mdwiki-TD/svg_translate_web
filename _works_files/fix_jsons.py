import json
from pathlib import Path


def process_json_files(directory_path: Path):
    # Ensure the directory exists
    if not directory_path.exists():
        print(f"Directory not found: {directory_path}")
        return

    # Iterate through all JSON files in the directory
    for file_path in directory_path.glob("*.json"):
        filename = file_path.name

        # Read JSON file
        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading file {filename}: {e}")
            continue

        # Target the data object (use 'result_data' key if present, otherwise root)
        result_data = data.get("result_data", data)
        modified = False

        # -------------------------------------------------------------
        # Case 1: Filename starts with crop_main_files
        # -------------------------------------------------------------
        if filename.startswith("crop_main_files"):
            _processed = result_data.get("files_processed") or result_data.get("pages_processed") or []

            result_data["pages_skipped"] = result_data.get("pages_skipped") or [
                item for item in _processed if item.get("status") == "skipped"
            ]
            result_data["pages_failed"] = result_data.get("pages_failed") or [
                item for item in _processed if item.get("status") == "failed"
            ]
            result_data["pages_uploaded"] = result_data.get("pages_uploaded") or [
                item for item in _processed if item.get("status") == "uploaded"
            ]
            result_data["pages_updated"] = result_data.get("pages_updated") or [
                item for item in _processed if item.get("status") == "updated"
            ]

            # Filter out items matching the 5 excluded statuses
            excluded_statuses = {
                "skipped",
                "failed",
                "success",
                "uploaded",
                "updated",
            }
            result_data["files_processed"] = [
                item for item in _processed if item.get("status") not in excluded_statuses
            ]

            modified = True

        # -------------------------------------------------------------
        # Case 2: Filename starts with create_owid_pages
        # -------------------------------------------------------------
        elif filename.startswith("create_owid_pages"):
            _processed = result_data.get("files_processed") or result_data.get("pages_processed") or []

            result_data["pages_skipped"] = result_data.get("pages_skipped") or [
                item for item in _processed if item.get("status") == "skipped"
            ]
            result_data["pages_failed"] = result_data.get("pages_failed") or [
                item for item in _processed if item.get("status") == "failed"
            ]
            result_data["pages_created"] = result_data.get("pages_created") or [
                item for item in _processed if item.get("status") == "created"
            ]
            result_data["pages_updated"] = result_data.get("pages_updated") or [
                item for item in _processed if item.get("status") == "updated"
            ]

            # Filter out items matching the 5 excluded statuses
            excluded_statuses = {
                "skipped",
                "failed",
                "success",
                "created",
                "updated",
            }
            result_data["pages_processed"] = [
                item for item in _processed if item.get("status") not in excluded_statuses
            ]

            modified = True

        # -------------------------------------------------------------
        # Case 3: Filename starts with rename_owid_pages
        # -------------------------------------------------------------
        elif filename.startswith("rename_owid_pages"):
            pages_processed = result_data.get("pages_processed") or []

            result_data["pages_renamed"] = result_data.get("pages_renamed") or [
                item for item in pages_processed if item.get("status") == "renamed"
            ]
            result_data["pages_skipped"] = result_data.get("pages_skipped") or [
                item for item in pages_processed if item.get("status") == "skipped_target_exists"
            ]
            result_data["pages_redirected"] = result_data.get("pages_redirected") or [
                item for item in pages_processed if item.get("status") == "redirected"
            ]
            result_data["pages_failed"] = result_data.get("pages_failed") or [
                item for item in pages_processed if item.get("status") == "failed"
            ]

            modified = True

        # -------------------------------------------------------------
        # Save modifications back to the file if processed
        # -------------------------------------------------------------
        if modified:
            with file_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Processed and updated file: {filename}")


# Target directory using pathlib
directory_path = Path("I:/TOOLFORGE_TOOLS/copy-svg-langs.toolforge.org/data/svg_jobs")
process_json_files(directory_path)
