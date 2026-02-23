# Technical Report: Replacing `download_file_from_commons` with `download_one_file`

**Date:** 2026-02-23
**Author:** Claude Code Analysis
**Status:** Technical Assessment

---

## Executive Summary

This report analyzes the feasibility of replacing the `download_file_from_commons` function (in `download_main_files_worker.py`) with the existing `download_one_file` function (in `tasks/downloads/download.py`). Both functions download files from Wikimedia Commons but have different design philosophies, interfaces, and capabilities.

---

## Function Comparison

### 1. `download_file_from_commons` (Current Implementation)

**Location:** `src/main_app/jobs_workers/download_main_files_worker.py:33`

**Signature:**

```python
def download_file_from_commons(
    filename: str,
    output_dir: Path,
    session: requests.Session | None = None,
) -> dict[str, Any]
```

**Return Value:**

```python
{
    "success": bool,
    "path": str | None,      # filename only (not full path)
    "size_bytes": int | None,
    "error": str | None,
}
```

**Key Features:**
| Feature | Description |
|---------|-------------|
| **Detailed Return** | Returns success flag, file size, path, and error message |
| **Filename Handling** | Strips "File:" prefix automatically |
| **URL Encoding** | Converts spaces to underscores for URLs |
| **Timeout** | 60 seconds |
| **Error Handling** | Distinguishes between network errors and unexpected errors |
| **Logging** | Info-level logging for success, error-level for failures |
| **Session Management** | Creates session with User-Agent if not provided |

---

### 2. `download_one_file` (Proposed Replacement)

**Location:** `src/main_app/tasks/downloads/download.py:19`

**Signature:**

```python
def download_one_file(
    title: str,
    out_dir: Path,
    i: int,                          # Required index for logging
    session: requests.Session = None,
    overwrite: bool = False          # Controls file overwrite behavior
) -> Dict[str, str]
```

**Return Value:**

```python
{
    "result": "success" | "existing" | "failed",
    "path": str,                     # full path when available
}
```

**Key Features:**
| Feature | Description |
|---------|-------------|
| **Existing File Check** | Skips download if file exists (unless `overwrite=True`) |
| **Overwrite Control** | Optional parameter to force re-download |
| **Index Parameter** | Required integer for log context (e.g., `[5] Downloaded: file.svg`) |
| **URL Encoding** | Uses `quote()` but doesn't convert spaces to underscores |
| **Timeout** | 30 seconds |
| **Error Handling** | Less granular (network vs non-200 status) |
| **Return Values** | Three-state result: success/existing/failed |
| **Logging** | Debug-level logging with index prefix |

---

## Strengths and Weaknesses Analysis

### `download_file_from_commons` Strengths

| Strength                              | Impact                                                    |
| ------------------------------------- | --------------------------------------------------------- |
| **Rich return data**                  | Provides `size_bytes` for monitoring and reporting        |
| **Detailed error messages**           | Distinguishes request errors from unexpected exceptions   |
| **Consistent filename normalization** | Handles "File:" prefix and space-to-underscore conversion |
| **Longer timeout**                    | 60s vs 30s - better for larger SVGs or slow connections   |
| **No external dependencies**          | Doesn't require tqdm or other libraries                   |
| **Comprehensive test coverage**       | 8 dedicated test cases covering edge cases                |

### `download_file_from_commons` Weaknesses

| Weakness                              | Impact                                          |
| ------------------------------------- | ----------------------------------------------- |
| **Always overwrites**                 | No option to skip existing files                |
| **Less integration with task system** | Designed for job workers, not the task pipeline |
| **Returns filename only**             | Returns just the filename, not full path        |

---

### `download_one_file` Strengths

| Strength                         | Impact                                          |
| -------------------------------- | ----------------------------------------------- |
| **Existing file handling**       | Built-in skip logic reduces redundant downloads |
| **Overwrite control**            | Flexible behavior via `overwrite` parameter     |
| **Task pipeline integration**    | Used throughout the translation task system     |
| **Standardized across codebase** | Already used in 8 locations                     |
| **Full path return**             | Returns complete path string                    |

### `download_one_file` Weaknesses

| Weakness                       | Impact                                                    |
| ------------------------------ | --------------------------------------------------------- |
| **Required index parameter**   | Forces callers to provide an index even when not batching |
| **No file size return**        | Missing `size_bytes` which is used in current reporting   |
| **Shorter timeout**            | 30s may fail on larger files                              |
| **No "File:" prefix handling** | Expects clean title without prefix                        |
| **Less granular errors**       | Doesn't distinguish error types in return value           |
| **Missing tests**              | No dedicated unit tests in test suite                     |
| **Debug-level logging only**   | Less visibility in production logs                        |

---

## Impact Analysis: Replacement Scenarios

### Scenario 1: Direct Replacement in `process_downloads()`

The current usage in `download_main_files_worker.py:189`:

```python
download_result = download_file_from_commons(
    clean_filename,
    output_dir,
    session=session,
)
```

**Required changes if using `download_one_file`:**

```python
download_result = download_one_file(
    clean_filename,
    output_dir,
    i=n,  # Would need to pass loop index
    session=session,
    overwrite=True,  # Current behavior always overwrites
)

# Adapt result handling:
# - Change: download_result["success"] -> download_result["result"] == "success"
# - Remove: download_result["size_bytes"] (not available)
# - Add logic: handle "existing" result state
```

**Breaking Changes:**

1. **Missing `size_bytes`** - Used in `file_info["size_bytes"]` for reporting
2. **Different result structure** - `"success"` boolean vs `"result"` string
3. **Different path return** - Full path vs filename only
4. **Existing file behavior** - Would need `overwrite=True` to match current behavior

---

## Recommendations

### Option 1: **Do Not Replace - Keep Both Functions** (Recommended)

**Rationale:**

-   The two functions serve different architectural layers:

    -   `download_file_from_commons`: Job worker layer (background batch jobs)
    -   `download_one_file`: Task pipeline layer (user-initiated translation tasks)

-   The job worker **needs** the extra metadata (`size_bytes`) for its reporting
-   The task pipeline **benefits** from the skip-existing optimization

**Action:** Keep both functions, but add a cross-reference comment:

```python
# Note: For task pipeline downloads, see download_one_file in
# src/main_app/tasks/downloads/download.py
```

---

### Option 2: **Enhance `download_one_file` and Migrate**

If consolidation is desired, enhance `download_one_file` first:

**Required enhancements:**

1. Make `i` parameter optional
2. Add `size_bytes` to return value
3. Add optional "File:" prefix stripping
4. Increase timeout or make it configurable
5. Add proper test coverage

**Migration effort:** Medium (2-3 days including testing)

---

### Option 3: **Extract Common Core, Keep Separate Interfaces**

Create a shared internal function used by both:

```python
# Internal implementation
def download_commons_file_core(...) -> dict: ...

# Public interfaces (thin wrappers)
def download_file_from_commons(...) -> dict: ...  # Rich metadata
def download_one_file(...) -> dict: ...           # Task-optimized
```

**Migration effort:** Low (1 day)

---

### Option 4: **Create `commons_client.py` with Core Download Function** (Recommended Alternative)

This approach creates a dedicated low-level module for Wikimedia Commons HTTP operations, providing a clean separation between network logic and business logic.

#### Proposed File Structure

**New File:** `src/main_app/utils/commons_client.py`

```python
"""Low-level Wikimedia Commons download utilities.

This module provides the core HTTP download functionality for fetching
files from Wikimedia Commons. It serves as the foundation for higher-level
download functions used across the application.
"""

from __future__ import annotations

import functools
import logging
import requests
from typing import TYPE_CHECKING
from urllib.parse import quote

if TYPE_CHECKING:
    import requests

logger = logging.getLogger("svg_translate")

BASE_COMMONS_URL = "https://commons.wikimedia.org/wiki/Special:FilePath/"


def download_commons_file_core(
    filename: str,
    session: requests.Session,
    timeout: int = 60,
) -> bytes | None:
    """Download a file from Wikimedia Commons and return raw content.

    This is the lowest-level download function that handles the actual HTTP
    request to Commons. It performs no file I/O, validation, or error handling.
    Callers are responsible for catching exceptions and handling failures.

    Args:
        filename: Clean filename without "File:" prefix. Spaces will be
            converted to underscores for the URL.
        session: Pre-configured requests Session with appropriate headers
            (User-Agent, etc.).
        timeout: Request timeout in seconds. Defaults to 60s for compatibility
            with larger SVG files.

    Returns:
        Raw bytes content of the downloaded file.

    Raises:
        requests.RequestException: On network errors, HTTP errors (4xx, 5xx),
            or timeouts.

    Example:
        >>> session = create_commons_session("MyBot/1.0")
        >>> try:
        ...     content = download_commons_file_core("Example.svg", session)
        ...     Path("Example.svg").write_bytes(content)
        ... except requests.RequestException as e:
        ...     logger.error(f"Download failed: {e}")
    """
    # Normalize filename: convert spaces to underscores for URL
    normalized_name = filename.replace(" ", "_")
    url = f"{BASE_COMMONS_URL}{quote(normalized_name)}"

    response = session.get(url, timeout=timeout, allow_redirects=True)
    response.raise_for_status()
    return response.content


@functools.lru_cache(maxsize=1)
def create_commons_session(user_agent: str | None = None) -> requests.Session:
    """Create a pre-configured requests Session for Commons API calls.

    Args:
        user_agent: Optional custom User-Agent string. If not provided,
            defaults to a generic bot identifier.

    Returns:
        Configured requests Session ready for use.
    """

    session = requests.Session()
    session.headers.update({
        "User-Agent": user_agent or "SVGTranslateBot/1.0",
    })
    return session
```

#### Refactored `download_file_from_commons`

**File:** `src/main_app/jobs_workers/download_main_files_worker.py`

```python
from ..utils.commons_client import download_commons_file_core, create_commons_session

def download_file_from_commons(
    filename: str,
    output_dir: Path,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Download a single file from Wikimedia Commons.

    Args:
        filename: The file name (e.g., "File:Example.svg")
        output_dir: Directory where the file should be saved
        session: Optional requests session to use

    Returns:
        dict with keys: success (bool), path (str|None), size_bytes (int|None),
        error (str|None)
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
    clean_filename = filename[5:] if filename.startswith("File:") else filename

    # Determine output path
    out_path = output_dir / clean_filename

    # Create session if not provided
    if session is None:
        session = create_commons_session(settings.oauth.user_agent)

    # Use the core download function
    try:
        content = download_commons_file_core(clean_filename, session, timeout=60)
    except Exception as e:
        result["error"] = f"Download failed: {str(e)}"
        logger.exception(f"Failed to download {clean_filename}")
        return result

    try:
        # Save the file
        out_path.write_bytes(content)
        file_size = len(content)

        result["success"] = True
        result["path"] = str(out_path.name)
        result["size_bytes"] = file_size
        logger.info(f"Downloaded: {clean_filename} ({file_size} bytes)")

    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
        logger.exception(f"Error saving {clean_filename}")

    return result
```

#### Refactored `download_one_file`

**File:** `src/main_app/tasks/downloads/download.py`

```python
from ...utils.commons_client import download_commons_file_core, create_commons_session

def download_one_file(
    title: str,
    out_dir: Path,
    i: int,
    session: requests.Session = None,
    overwrite: bool = False
) -> Dict[str, str]:
    """Download a single Commons file, skipping already-downloaded copies.

    Parameters:
        title: Title of the file page on Wikimedia Commons.
        out_dir: Directory where the file should be stored.
        i: 1-based index used only for logging context.
        session: Optional shared session.
        overwrite: Whether to overwrite existing files.

    Returns:
        dict: Outcome with keys ``result`` ("success", "existing", or
        "failed") and ``path`` (path string when available).
    """
    data = {
        "result": "",
        "path": "",
    }

    if not title:
        return data

    out_path = out_dir / title

    if out_path.exists() and not overwrite:
        logger.debug(f"[{i}] Skipped existing: {title}")
        data["result"] = "existing"
        data["path"] = str(out_path)
        return data

    if not session:
        session = create_commons_session(settings.oauth.user_agent)

    # Use the core download function with shorter timeout
    try:
        content = download_commons_file_core(title, session, timeout=30)
    except Exception as e:
        data["result"] = "failed"
        logger.error(f"[{i}] Failed: {title} -> {e}")
        return data

    try:
        out_path.write_bytes(content)
        logger.debug(f"[{i}] Downloaded: {title}")
        data["result"] = "success"
        data["path"] = str(out_path)
    except Exception as e:
        data["result"] = "failed"
        logger.error(f"[{i}] Failed to save: {title} -> {e}")

    return data
```

#### Benefits of This Approach

| Benefit                   | Description                                                                                          |
| ------------------------- | ---------------------------------------------------------------------------------------------------- |
| **Single Responsibility** | The core function does one thing: HTTP download. File I/O and business logic are handled by callers. |
| **Testability**           | The core function can be unit tested with mocked sessions without touching the filesystem.           |
| **Flexibility**           | Callers control timeout, error handling, logging level, and file operations independently.           |
| **No Code Duplication**   | URL construction, error handling, and session management are centralized.                            |
| **Type Safety**           | The core function has a simple signature returning `bytes`, with exceptions for error handling.      |

#### Migration Steps

1. **Create the new file:**

    ```bash
    mkdir -p src/main_app/utils
    touch src/main_app/utils/__init__.py
    touch src/main_app/utils/commons_client.py
    ```

2. **Add the core function** to `commons_client.py` with full docstrings.

3. **Refactor `download_file_from_commons`:**

    - Import `download_commons_file_core`
    - Replace the inline `session.get()` call with the core function
    - Keep all existing return value handling and logging

4. **Refactor `download_one_file`:**

    - Import `download_commons_file_core`
    - Replace the inline `session.get()` call with the core function
    - Keep existing file existence check and result handling

5. **Add tests** for the core function in `tests/app/utils/test_commons_client.py`.

6. **Verify** both existing test suites still pass:
    ```bash
    pytest tests/app/jobs_workers/test_download_main_files_worker.py -v
    pytest tests/app/tasks/downloads/ -v
    ```

#### Migration Effort

-   **Time:** 1-2 days
-   **Complexity:** Low
-   **Risk:** Very Low (thin wrapper refactoring)
-   **Testing:** Existing tests provide regression coverage; new unit tests for core function

---

## Conclusion

| Aspect                             | Assessment                                    |
| ---------------------------------- | --------------------------------------------- |
| **Direct replacement feasibility** | Not recommended without modifications         |
| **Code consolidation benefit**     | Low - different use cases                     |
| **Risk of replacement**            | Medium - breaking changes to reporting        |
| **Recommended approach**           | Keep both, add documentation cross-references |

The functions have evolved to serve different purposes within the application architecture. While they appear duplicative, each is optimized for its specific context. Replacing one with the other would either lose important functionality or require significant refactoring of the replacement function.

---

## Appendix: Usage Locations

### `download_file_from_commons`

-   `src/main_app/jobs_workers/download_main_files_worker.py:189` - Main usage in `process_downloads()`

### `download_one_file`

-   `src/main_app/tasks/downloads/download.py` - Definition
-   `src/main_app/app_routes/extract/routes.py` - Extract feature
-   `src/main_app/app_routes/fix_nested/fix_utils.py` - Fix nested feature
-   `src/main_app/tasks/extract/extract_task.py` - Extract task
-   Multiple test files
