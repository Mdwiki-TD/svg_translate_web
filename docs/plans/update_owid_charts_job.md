# PLAN: Update OWID Charts Background Job

## Overview

Create a new admin-only background job (`update_owid_charts`) that fetches metadata from
`https://ourworldindata.org/grapher/{slug}.metadata.json` for each `OwidChartRecord`,
extracts `timespan` from the metadata, parses it into `min_time` / `max_time` / `len_years`,
and updates the database record when values have changed.

---

## 1. Files to Create

| #   | File                                                                  | Purpose                             |
| --- | --------------------------------------------------------------------- | ----------------------------------- |
| 1   | `src/main_app/jobs_workers/update_owid_charts/__init__.py`            | Exports entry-point function        |
| 2   | `src/main_app/jobs_workers/update_owid_charts/worker.py`              | Worker class + entry-point function |
| 3   | `src/templates/jobs_templates/admin/update_owid_charts/list.html`    | Job list template                   |
| 4   | `src/templates/jobs_templates/admin/update_owid_charts/details.html` | Job detail template                 |

## 2. Files to Modify

| #   | File                                        | Change                                                                              |
| --- | ------------------------------------------- | ----------------------------------------------------------------------------------- |
| 1   | `src/main_app/jobs_workers/workers_list.py` | Register new job in `jobs_data_admins` |
| 2   | `src/main_app/app_routes/admin/sidebar.py`  | Add `Update OWID Charts` menu item under `"Jobs"` group                             |

---

## 3. Worker Design (`worker.py`)

### 3.1 Class: `UpdateOwidChartsWorker(BaseJobWorker)`

#### Required overrides

| Method                 | Return                                                             |
| ---------------------- | ------------------------------------------------------------------ |
| `get_job_type()`       | `"update_owid_charts"`                                             |
| `get_initial_result()` | Dict with `status`, timestamps, `summary`, `charts_processed` list |
| `process()`            | Main loop — see §3.2                                               |

#### No `user` / `site` needed

This job only does HTTP fetches to ourworldindata.org and DB updates. No MediaWiki auth
required. The constructor can ignore `user`.

### 3.2 `process()` Flow

```
1. Load all OwidChartRecords via list_charts()
2. Set result["summary"]["total"] = len(charts)
3. Calculate save-progress interval: self.get_priority(len(charts))
4. For n, chart in enumerate(charts, 1):
   a. If self.is_cancelled(): break
   b. Fetch https://ourworldindata.org/grapher/{chart.slug}.metadata.json
      - Use requests.get(timeout=15)
      - On network error: mark as failed, record error, continue
   c. Parse response JSON
   d. Find first column entry that has a "timespan" key
      - Iterate over response["columns"].values()
      - If no column has timespan → status "skipped_no_timespan", continue
   e. Parse timespan string (see §3.4)
   f. Compare parsed (min_time, max_time, len_years) with chart record's current values
      - If all three match → status "skipped", continue
   g. Call update_chart_data(chart.chart_id, {min_time, max_time, len_years})
      - On DB error: mark as failed, record error, continue
   h. Append ChartUpdateInfo to result["charts_processed"]
      - Record old/new values for display
5. Save progress every N items
6. Set result["status"] = "completed"
7. Return result
```

### 3.3 Dataclass: `ChartUpdateInfo`

```python
@dataclass
class ChartUpdateInfo:
    chart_id: int
    slug: str
    title: str
    status: str  # "updated" | "skipped" | "failed" | "skipped_no_timespan"
    old_min_time: int | None = None
    old_max_time: int | None = None
    old_len_years: int | None = None
    new_min_time: int | None = None
    new_max_time: int | None = None
    new_len_years: int | None = None
    error: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {...}
```

### 3.4 Timespan Parsing

Timespan format: `"YYYY-YYYY"` (e.g. `"2000-2022"`)

```python
def parse_timespan(timespan: str) -> tuple[int, int, int]:
    """Parse 'YYYY-YYYY' into (min_time, max_time, len_years)."""
    parts = timespan.split("-")
    # Handle "2000-2022" → min=2000, max=2022
    # Handle "2022" (single year) → min=2022, max=2022, len=1
    # Handle "2000-2022-..." take first two parts
    if len(parts) >= 2:
        y1 = int(parts[0])
        y2 = int(parts[1])
        return y1, y2, y2 - y1 + 1
    else:
        y = int(parts[0])
        return y, y, 1
```

Edge cases to handle:

-   Negative years (BCE): not expected in OWID data, but safe to pass through
-   Non-numeric parts: catch `ValueError` → skip as "failed"
-   Empty/missing timespan: handled by "no timespan" skip in column loop

### 3.5 HTTP Fetch Error Handling

| Scenario              | Action                                                    |
| --------------------- | --------------------------------------------------------- |
| Network timeout (15s) | `failed`, record `error = "Network timeout"`              |
| HTTP 404              | `failed`, record `error = "Metadata not found (404)"`     |
| HTTP 5xx              | `failed`, record `error = f"Server error: {status_code}"` |
| Invalid JSON          | `failed`, record `error = "Invalid JSON response"`        |
| No `columns` key      | `failed`, record `error = "No columns in metadata"`       |

Add a small delay between requests (0.3s) to be polite to ourworldindata.org servers.

### 3.6 Initial Result Structure

```python
{
    "status": "pending",
    "started_at": datetime.now().isoformat(),
    "completed_at": None,
    "cancelled_at": None,
    "summary": {
        "total": 0,
        "processed": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "skipped_no_timespan": 0,
    },
    "charts_processed": [],
}
```

### 3.7 Entry-Point Function

```python
def update_owid_charts_for_templates(
    job_id: int,
    user: Dict[str, Any] | None = None,
    *,
    cancel_event: threading.Event | None = None,
    args: Dict[str, Any] | None = None,
) -> None:
    logger.info(f"Starting job {job_id}: update OWID charts metadata")
    worker = UpdateOwidChartsWorker(job_id, user, cancel_event)
    worker.run()
```

---

## 4. Registration

### 4.1 `workers_list.py`

Add three entries:

```python
# Import (top)
from .update_owid_charts import update_owid_charts_for_templates

# jobs_data_admins dict entry
"update_owid_charts": JobData(
    job_type="update_owid_charts",
    job_name="Update OWID Charts",
    job_details_template="jobs_templates/admin/update_owid_charts/details.html",
    job_list_template="jobs_templates/admin/update_owid_charts/list.html",
    job_callable=update_owid_charts_for_templates,
),
```

### 4.2 `sidebar.py`

Add under `"Jobs"` group (before or after existing items, maintain alphabetical order):

```python
SidebarItem(
    id="update_owid_charts",
    admin=1,
    href=_safe_url_for(
        "admin.jobs.jobs_list",
        "/admin/jobs/update_owid_charts",
        job_type="update_owid_charts",
    ),
    title="Update OWID Charts",
    icon="bi-cloud-download",
),
```

### 4.3 `__init__.py` for the job package

```python
from __future__ import annotations

from .worker import update_owid_charts_for_templates

__all__ = ["update_owid_charts_for_templates"]
```

---

## 5. Templates

### 5.1 `list.html`

Follows the exact pattern of other list templates — extend `base_list.html`,
set `job_type`, override title/headline/confirm message.

### 5.2 `details.html`

Extends `base_details.html`. Has two blocks:

#### `job_summary`

Cards for: Total, Processed, Updated, Skipped, Skipped (no timespan), Failed.

#### `job_details`

A single card with a table showing all processed charts. Columns:

| # | Slug | Title | Old min_time | New min_time | Old max_time | New max_time | Old len_years | New len_years | Status | Error |

-   Slug links to `https://ourworldindata.org/grapher/{slug}`
-   Old/New columns show `–` when value is `None`
-   Status uses colored badges: `success` (updated), `secondary` (skipped), `warning` (skipped_no_timespan), `danger` (failed)
-   Error column shows error message for failed items, `–` otherwise

---

## 6. Result JSON Example

```json
{
    "status": "completed",
    "started_at": "2026-05-24T10:00:00",
    "completed_at": "2026-05-24T10:05:30",
    "cancelled_at": null,
    "summary": {
        "total": 150,
        "processed": 150,
        "updated": 23,
        "skipped": 112,
        "failed": 10,
        "skipped_no_timespan": 5
    },
    "charts_processed": [
        {
            "chart_id": 1,
            "slug": "share-of-final-energy-consumption-from-renewable-sources",
            "title": "Share of final energy use that comes from renewable sources",
            "status": "updated",
            "old_min_time": null,
            "old_max_time": null,
            "old_len_years": null,
            "new_min_time": 2000,
            "new_max_time": 2022,
            "new_len_years": 23,
            "error": null,
            "timestamp": "2026-05-24T10:00:01"
        }
    ]
}
```

---

## 7. Dependencies

-   `requests` — already in `requirements.txt` (line 12)
-   `src/main_app/db/services/owid_charts_service.py` — `list_charts()`, `update_chart_data()` already exist
-   `src/main_app/db/models/owid_charts.py` — `OwidChartRecord` model already exists
-   `src/main_app/jobs_workers/base_worker.py` — `BaseJobWorker` base class already exists

No new dependencies needed.

---

## 8. Testing Notes

Tests to write (in `tests/`):

1. `tests/unit/jobs_workers/test_update_owid_charts_worker.py` — test `parse_timespan()`, test worker logic with mocked HTTP responses
2. Integration test: mock `requests.get` and `list_charts()`, verify `update_chart_data()` is called with correct values

Test file should follow existing test naming conventions:

-   `tests/unit/jobs_workers/update_owid_charts/test_worker.py`

---

## 9. Sequence of Implementation

1. Create `__init__.py`
2. Create `worker.py` with `UpdateOwidChartsWorker` class and entry point
3. Register in `workers_list.py`
4. Add sidebar item in `sidebar.py`
5. Create templates (`list.html`, `details.html`)
6. Run `pytest` to verify nothing breaks
7. Run `black .` and `isort .` for formatting

---

## 10. Job Lifecycle Summary

```
User clicks "Start New Job" on /admin/jobs/update_owid_charts
  → POST /admin/jobs/update_owid_charts/start
  → jobs_worker.start_job(user, "update_owid_charts")
  → creates JobRecord (status=pending), spawns thread
  → thread runs UpdateOwidChartsWorker.run()
  → before_run() → updates status to "running"
  → process() → fetches metadata for each chart, updates DB, saves progress
  → after_run() → updates status to "completed" (or "failed"/"cancelled")
```
