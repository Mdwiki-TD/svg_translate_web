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
def _download_commons_file_core(...) -> dict: ...

# Public interfaces (thin wrappers)
def download_file_from_commons(...) -> dict: ...  # Rich metadata
def download_one_file(...) -> dict: ...           # Task-optimized
```

**Migration effort:** Low (1 day)

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
