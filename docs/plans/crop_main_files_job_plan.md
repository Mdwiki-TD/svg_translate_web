# Plan: Crop Main Files Job Implementation

## Overview

Implement a new admin-only background job endpoint for cropping main files and uploading them with new names (e.g., `File:death rate from obesity, World, 2021.svg` → `File:death rate from obesity, World, 2021 (cropped).svg`).

This follows the same design pattern as existing jobs: `collect_main_files`, `download_main_files`, and `fix_nested_main_files`.

---

## Implementation Checklist

### Phase 1: Core Worker
- [x] Create [`src/main_app/jobs_workers/crop_main_files/__init__.py`](src/main_app/jobs_workers/crop_main_files/__init__.py)
  - [x] Implement `generate_cropped_filename()` - name transformation
  - [ ] Implement `crop_svg_file()` - SVG cropping logic (TODO: full implementation)
  - [ ] Implement `upload_cropped_file()` - Commons upload (TODO: full implementation)
  - [x] Implement `process_crops()` - main processing loop (placeholder done)
  - [x] Implement `crop_main_files_for_templates()` - entry point (placeholder done)

### Phase 2: Templates
- [x] Create [`src/templates/admins/crop_main_files_jobs.html`](src/templates/admins/crop_main_files_jobs.html) - list view
- [x] Create [`src/templates/admins/crop_main_files_job_detail.html`](src/templates/admins/crop_main_files_job_detail.html) - detail view

### Phase 3: Integration
- [x] Modify [`src/main_app/jobs_workers/jobs_worker.py`](src/main_app/jobs_workers/jobs_worker.py)
  - [x] Import `crop_main_files_for_templates`
  - [x] Add to `jobs_targets` dictionary
- [x] Modify [`src/main_app/app_routes/admin/admin_routes/jobs.py`](src/main_app/app_routes/admin/admin_routes/jobs.py)
  - [x] Add to `JOB_TYPE_TEMPLATES`
  - [x] Add to `JOB_TYPE_LIST_TEMPLATES`
- [x] Modify [`src/main_app/app_routes/admin/sidebar.py`](src/main_app/app_routes/admin/sidebar.py)
  - [x] Add "Crop Main Files" sidebar menu item

### Phase 4: Testing
- [ ] Create [`tests/app/jobs_workers/test_crop_main_files/__init__.py`](tests/app/jobs_workers/test_crop_main_files/__init__.py)
  - [ ] Test `generate_cropped_filename()`
  - [ ] Test `crop_svg_file()` success/failure cases
  - [ ] Test `upload_cropped_file()` success/failure cases
  - [ ] Test job cancellation
  - [ ] Test full workflow

### Phase 5: Verification
- [x] Verify endpoints accessible at `/admin/jobs/crop_main_files/*`
- [ ] Test job start from admin UI (needs full worker implementation)
- [ ] Test job cancellation (needs full worker implementation)
- [ ] Test job deletion (needs full worker implementation)
- [ ] Verify results display correctly (needs full worker implementation)

---

## Files to Create

### 1. Worker Module

**File:** [`src/main_app/jobs_workers/crop_main_files/__init__.py`](src/main_app/jobs_workers/crop_main_files/__init__.py)

**Purpose:** Core worker logic for cropping main files and uploading them to Commons.

**Key Functions:**
- `crop_svg_file(file_path: Path, crop_box: tuple[float, float, float, float]) -> bool` - Crop SVG using viewBox manipulation
- `upload_cropped_file(original_filename: str, cropped_path: Path, user: Any) -> dict` - Upload cropped file with new name
- `generate_cropped_filename(filename: str) -> str` - Transform "File:X.svg" → "File:X (cropped).svg"
- `process_crops(job_id, result, result_file, crop_config, cancel_event)` - Main processing loop
- `crop_main_files_for_templates(job_id, user, cancel_event)` - Entry point function

**Result Data Structure:**
```python
{
    "status": "completed|failed|cancelled",
    "started_at": "ISO timestamp",
    "completed_at": "ISO timestamp",
    "cancelled_at": "ISO timestamp|null",
    "summary": {
        "total": int,
        "processed": int,
        "cropped": int,
        "uploaded": int,
        "failed": int,
        "skipped": int
    },
    "files_processed": [
        {
            "original_file": str,
            "cropped_file": str,
            "status": "uploaded|failed|skipped",
            "timestamp": str,
            "reason": str|null,
            "error": str|null
        }
    ]
}
```

---

### 2. HTML Templates

**File:** [`src/templates/admins/crop_main_files_jobs.html`](src/templates/admins/crop_main_files_jobs.html)

**Purpose:** List view for crop jobs (similar to [`collect_main_files_jobs.html`](src/templates/admins/collect_main_files_jobs.html)).

**Features:**
- Table showing job ID, status, timestamps
- "Start New Job" button with POST form
- View/Cancel/Delete actions per job
- Confirmation dialogs

---

**File:** [`src/templates/admins/crop_main_files_job_detail.html`](src/templates/admins/crop_main_files_job_detail.html)

**Purpose:** Detail view for individual crop jobs (similar to [`collect_main_files_job_detail.html`](src/templates/admins/collect_main_files_job_detail.html)).

**Features:**
- Job metadata display (status, timestamps, result file)
- Summary cards: Total, Processed, Cropped, Uploaded, Failed, Skipped
- Detailed results table showing:
  - Original filename
  - Cropped filename (new name)
  - Status badge
  - Error/reason messages
- Cancel/Delete/Back actions

---

### 3. Tests

**File:** [`tests/app/jobs_workers/test_crop_main_files/__init__.py`](tests/app/jobs_workers/test_crop_main_files/__init__.py)

**Test Cases:**
- `test_generate_cropped_filename()` - Name transformation logic
- `test_crop_svg_file_success()` - SVG cropping with valid input
- `test_crop_svg_file_invalid_box()` - Error handling for invalid crop
- `test_upload_cropped_file_success()` - Successful upload flow
- `test_upload_cropped_file_failure()` - Upload error handling
- `test_process_crops_cancellation()` - Job cancellation mid-process
- `test_crop_main_files_for_templates()` - Full workflow test

---

## Files to Modify

### 4. Jobs Worker Registry

**File:** [`src/main_app/jobs_workers/jobs_worker.py`](src/main_app/jobs_workers/jobs_worker.py)

**Changes:**
- Import `crop_main_files_for_templates` from new worker module
- Add `"crop_main_files"` entry to `jobs_targets` dictionary (line 64-68)

```python
from .crop_main_files import crop_main_files_for_templates

jobs_targets = {
    "fix_nested_main_files": fix_nested_main_files_for_templates,
    "collect_main_files": collect_main_files_for_templates,
    "download_main_files": download_main_files_for_templates,
    "crop_main_files": crop_main_files_for_templates,  # NEW
}
```

---

### 5. Admin Routes

**File:** [`src/main_app/app_routes/admin/admin_routes/jobs.py`](src/main_app/app_routes/admin/admin_routes/jobs.py)

**Changes:**

Add to `JOB_TYPE_TEMPLATES` dictionary (line 29-33):
```python
JOB_TYPE_TEMPLATES = {
    "collect_main_files": "admins/collect_main_files_job_detail.html",
    "fix_nested_main_files": "admins/fix_nested_main_files_job_detail.html",
    "download_main_files": "admins/download_main_files_job_detail.html",
    "crop_main_files": "admins/crop_main_files_job_detail.html",  # NEW
}
```

Add to `JOB_TYPE_LIST_TEMPLATES` dictionary (line 88-92):
```python
JOB_TYPE_LIST_TEMPLATES = {
    "collect_main_files": "admins/collect_main_files_jobs.html",
    "fix_nested_main_files": "admins/fix_nested_main_files_jobs.html",
    "download_main_files": "admins/download_main_files_jobs.html",
    "crop_main_files": "admins/crop_main_files_jobs.html",  # NEW
}
```

---

### 6. Admin Sidebar

**File:** [`src/main_app/app_routes/admin/sidebar.py`](src/main_app/app_routes/admin/sidebar.py)

**Changes:**
Add new menu item to sidebar items list (around line 33-51):

```python
{
    "id": "crop_main_files_jobs",
    "admin": 1,
    "href": "crop_main_files/list",
    "title": "Crop Main Files",
    "icon": "bi-crop",  # Bootstrap Icons class
},
```

---

## API Endpoints

The following endpoints will be automatically available via existing route handlers:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/jobs/crop_main_files/list` | List all crop jobs |
| POST | `/admin/jobs/crop_main_files/start` | Start new crop job |
| GET | `/admin/jobs/crop_main_files/<int:job_id>` | View job details |
| POST | `/admin/jobs/crop_main_files/<int:job_id>/cancel` | Cancel running job |
| POST | `/admin/jobs/crop_main_files/<int:job_id>/delete` | Delete job record |

---

## Implementation Notes

### SVG Cropping Strategy

1. **Download original file** from Wikimedia Commons to temp directory
2. **Parse SVG** to get current dimensions
3. **Modify viewBox** attribute to crop (or add crop transform)
4. **Save cropped version** with new filename pattern: `File:X (cropped).svg`
5. **Upload to Commons** using existing wiki client

### Name Transformation

```python
def generate_cropped_filename(filename: str) -> str:
    """
    Transform filename to cropped version.

    Examples:
        "File:death rate from obesity, World, 2021.svg"
        → "File:death rate from obesity, World, 2021 (cropped).svg"

        "File:Chart showing data.svg"
        → "File:Chart showing data (cropped).svg"
    """
    # Remove "File:" prefix, add " (cropped)" before extension
    if filename.startswith("File:"):
        base = filename[5:]  # Remove "File:"
    else:
        base = filename

    # Split extension and insert " (cropped)"
    if "." in base:
        name, ext = base.rsplit(".", 1)
        return f"File:{name} (cropped).{ext}"
    return f"File:{base} (cropped)"
```

### Crop Configuration

For initial implementation, crop bounds can be passed as:
- Query parameters when starting job
- Hardcoded defaults for common crop scenarios
- Configurable via admin form (future enhancement)

Example crop config:
```python
{
    "crop_box": (10, 10, 500, 500),  # x, y, width, height
    "unit": "px"  # pixels
}
```

---

## Security Considerations

- All endpoints require admin authentication (handled by existing `@admin_required` decorator)
- OAuth token required for Commons uploads
- Job cancellation support to prevent runaway processes
- Rate limiting consideration for bulk uploads

---

## Future Enhancements

1. **Interactive crop selection** - Preview and select crop region before job
2. **Template filtering** - Crop only specific template categories
3. **Batch size limits** - Process in smaller batches with delays
4. **Upload verification** - Verify cropped files uploaded successfully
5. **Rollback capability** - Delete cropped files if needed
