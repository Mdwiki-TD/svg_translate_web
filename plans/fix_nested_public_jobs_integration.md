# Integration Plan: Fix Nested Tasks into Public Jobs Workers

## Overview

This plan describes how to integrate the "Fix Nested Tasks" functionality into the `public_jobs_workers` system, making it accessible to regular users (not just admins). Currently, `fix_nested_main_files` is an admin-only job located in [`src/main_app/jobs_workers/fix_nested_main_files_worker.py`](src/main_app/jobs_workers/fix_nested_main_files_worker.py:1). The goal is to create a public-facing version that allows users to fix nested tags in specific SVG files they submit.

## Current Architecture Analysis

### Admin Jobs (Current Location)

```
src/main_app/jobs_workers/
├── fix_nested_main_files_worker.py   # Admin job: processes ALL templates
├── jobs_worker.py                    # Job runner (start_job, start_job_with_args)
├── workers_list.py                   # Registry: jobs_targets (admin), jobs_targets_public (public)
└── base_worker.py                    # Base class for all workers
```

### Public Jobs (Target Location)

```
src/main_app/public_jobs_workers/
├── copy_svg_langs/                   # Example public job structure
│   ├── __init__.py
│   ├── job.py                        # Processor class (CopySvgLangsProcessor)
│   ├── service.py                    # Service layer (start_copy_svg_langs_job)
│   ├── worker.py                     # Worker class + entry point
│   └── steps/                        # Pipeline steps
│       ├── fix_nested.py             # Already has fix_nested step!
│       └── ...
└── __init__.py
```

### Current Fix Nested Routes

```
src/main_app/app_routes/fix_nested/
├── routes.py                         # Web routes for single file fix
└── worker.py                         # Core functions (download_svg_file, fix_nested_tags, etc.)
```

## Key Differences: Admin vs Public Fix Nested

| Aspect         | Admin (fix_nested_main_files)                  | Public (fix_nested_tasks)                |
| -------------- | ---------------------------------------------- | ---------------------------------------- |
| Scope          | All templates in database                      | User-submitted file(s)                   |
| Input          | None (iterates all templates)                  | Filename or file list                    |
| Authentication | Admin OAuth                                    | User OAuth                               |
| Tracking       | Job-based                                      | Job-based (new)                          |
| Templates      | `admins/jobs_templates/fix_nested_main_files/` | `jobs_templates/fix_nested_tasks/` (new) |

## Architecture Diagram

```mermaid
graph TB
    subgraph Public Jobs Workers
        A[fix_nested_tasks/worker.py] --> B[FixNestedTasksWorker]
        A --> C[fix_nested_tasks_worker_entry]
        B --> D[FixNestedTasksProcessor]
    end

    subgraph Service Layer
        E[service.py] --> F[start_fix_nested_tasks_job]
        F --> G[jobs_worker.start_job_with_args]
    end

    subgraph Registry
        H[workers_list.py] --> I[jobs_targets_public]
        I --> C
    end

    subgraph Routes
        J[public_jobs.py] --> K[/jobs/fix_nested_tasks/start_with_args]
        K --> L[Form with filename]
    end

    subgraph Shared Utils
        M[fix_nested/worker.py] --> N[download_svg_file]
        M --> O[fix_nested_tags]
        M --> P[upload_fixed_svg]
    end

    D --> N
    D --> O
    D --> P
    G --> H
    L --> E
```

## Implementation Plan

### Phase 1: Create Public Worker Structure

#### 1.1 Create Directory Structure

Create new directory: `src/main_app/public_jobs_workers/fix_nested_tasks/`

Files to create:

-   `__init__.py` - Module initialization
-   `worker.py` - Worker class and entry point
-   `job.py` - Processor class with pipeline logic
-   `service.py` - Service layer for job initiation

#### 1.2 Create Templates

Create directory: `src/templates/jobs_templates/fix_nested_tasks/`

Files to create:

-   `details.html` - Job detail page (based on `copy_svg_langs/details.html`)
-   `list.html` - Job list page (based on `copy_svg_langs/list.html`)

### Phase 2: Implement Worker Components

#### 2.1 Worker Implementation (`fix_nested_tasks/worker.py`)

The worker should follow the pattern of [`CopySvgLangsWorker`](src/main_app/public_jobs_workers/copy_svg_langs/worker.py:18):

```python
class FixNestedTasksWorker(BaseJobWorker):
    """Worker for fixing nested tags in user-submitted SVG files."""

    def get_job_type(self) -> str:
        return "fix_nested_tasks"

    def get_initial_result(self) -> dict:
        return {
            "status": "pending",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "title": self.title,
            "stages": {
                "download": {"status": "Pending", "message": "Downloading files"},
                "analyze": {"status": "Pending", "message": "Analyzing nested tags"},
                "fix": {"status": "Pending", "message": "Fixing nested tags"},
                "verify": {"status": "Pending", "message": "Verifying fixes"},
                "upload": {"status": "Pending", "message": "Uploading fixed files"},
            },
            "summary": {},
            "results": [],
        }

    def process(self) -> dict:
        processor = FixNestedTasksProcessor(...)
        return processor.run()

def fix_nested_tasks_worker_entry(task_id, title, args, user, *, cancel_event=None):
    """Entry point for the background job."""
    worker = FixNestedTasksWorker(...)
    worker.run()
```

#### 2.2 Processor Implementation (`fix_nested_tasks/job.py`)

The processor should handle:

1. **Input parsing**: Extract filename(s) from args
2. **Download stage**: Download SVG file(s) from Commons
3. **Analyze stage**: Detect nested tags using `match_nested_tags`
4. **Fix stage**: Apply fixes using `fix_nested_file`
5. **Verify stage**: Confirm fixes were applied
6. **Upload stage**: Upload fixed files back to Commons

Key functions to reuse from [`fix_nested/worker.py`](src/main_app/app_routes/fix_nested/worker.py:21):

-   `download_svg_file()`
-   `detect_nested_tags()`
-   `fix_nested_tags()`
-   `verify_fix()`
-   `upload_fixed_svg()`

#### 2.3 Service Implementation (`fix_nested_tasks/service.py`)

Follow pattern from [`copy_svg_langs/service.py`](src/main_app/public_jobs_workers/copy_svg_langs/service.py:16):

```python
def start_fix_nested_tasks_job(
    title: str,
    args: dict,
    user: dict | None = None,
) -> int:
    """Start a background job to fix nested tags."""
    username = user.get("username") if user else None
    job = jobs_service.create_job("fix_nested_tasks", username)

    cancel_event = threading.Event()
    _register_cancel_event(job.id, cancel_event)

    thread = threading.Thread(
        target=_runner,
        args=(job.id, title, args, user, cancel_event, fix_nested_tasks_worker_entry),
        daemon=True,
    )
    thread.start()

    return job.id
```

### Phase 3: Register in Workers List

#### 3.1 Update [`workers_list.py`](src/main_app/jobs_workers/workers_list.py:1)

Add to `jobs_targets_public`:

```python
from ..public_jobs_workers.fix_nested_tasks.worker import fix_nested_tasks_worker_entry

jobs_targets_public = {
    "copy_svg_langs": copy_svg_langs_worker_entry,
    "fix_nested_tasks": fix_nested_tasks_worker_entry,  # NEW
}
```

Add to `JOB_TYPE_TEMPLATES_PUBLIC`:

```python
JOB_TYPE_TEMPLATES_PUBLIC = {
    "copy_svg_langs": "jobs_templates/copy_svg_langs/details.html",
    "fix_nested_tasks": "jobs_templates/fix_nested_tasks/details.html",  # NEW
}
```

Add to `JOB_TYPE_LIST_TEMPLATES_PUBLIC`:

```python
JOB_TYPE_LIST_TEMPLATES_PUBLIC = {
    "copy_svg_langs": "jobs_templates/copy_svg_langs/list.html",
    "fix_nested_tasks": "jobs_templates/fix_nested_tasks/list.html",  # NEW
}
```

### Phase 4: Create Templates

#### 4.1 Job List Template (`jobs_templates/fix_nested_tasks/list.html`)

Based on [`copy_svg_langs/list.html`](src/templates/jobs_templates/copy_svg_langs/list.html:1), should include:

-   List of jobs with status
-   Start new job button with form
-   Job ID, title, status, created_at columns
-   Cancel/Delete actions

#### 4.2 Job Detail Template (`jobs_templates/fix_nested_tasks/details.html`)

Based on [`copy_svg_langs/details.html`](src/templates/jobs_templates/copy_svg_langs/details.html:1), should include:

-   Job status display
-   Stage progress indicators
-   Results summary
-   Per-file results (filename, status, tags fixed, etc.)

### Phase 5: Update Public Jobs Routes

#### 5.1 Verify Route Compatibility

The existing routes in [`public_jobs.py`](src/main_app/app_routes/public_jobs.py:175) should work automatically once the job type is registered:

-   `/jobs/fix_nested_tasks/list` - Job list
-   `/jobs/fix_nested_tasks/start_with_args` - Start job with form data
-   `/jobs/fix_nested_tasks/<job_id>` - Job detail
-   `/jobs/fix_nested_tasks/<job_id>/cancel` - Cancel job

### Phase 6: Testing

#### 6.1 Unit Tests

Create: `tests/unit/public_jobs_workers/fix_nested_tasks/`

-   `test_fix_nested_tasks_worker.py`
-   `test_fix_nested_tasks_processor.py`
-   `test_fix_nested_tasks_service.py`

#### 6.2 Integration Tests

Create: `tests/integration/app_routes/main_routes/fix_nested_tasks/`

-   `test_fix_nested_tasks_routes.py`

## File Structure After Implementation

```
src/main_app/public_jobs_workers/
├── __init__.py
├── copy_svg_langs/
│   └── ...
└── fix_nested_tasks/                    # NEW
    ├── __init__.py
    ├── job.py                           # NEW: Processor
    ├── service.py                       # NEW: Service layer
    └── worker.py                        # NEW: Worker + entry point

src/templates/jobs_templates/
├── copy_svg_langs/
│   ├── details.html
│   └── list.html
└── fix_nested_tasks/                    # NEW
    ├── details.html                     # NEW
    └── list.html                        # NEW

tests/unit/public_jobs_workers/
├── copy_svg_langs/
│   └── ...
└── fix_nested_tasks/                    # NEW
    ├── test_fix_nested_tasks_worker.py
    ├── test_fix_nested_tasks_processor.py
    └── test_fix_nested_tasks_service.py
```

## Detailed Todo List

-   [ ] Create `src/main_app/public_jobs_workers/fix_nested_tasks/__init__.py`
-   [ ] Create `src/main_app/public_jobs_workers/fix_nested_tasks/worker.py` with FixNestedTasksWorker class
-   [ ] Create `src/main_app/public_jobs_workers/fix_nested_tasks/job.py` with FixNestedTasksProcessor class
-   [ ] Create `src/main_app/public_jobs_workers/fix_nested_tasks/service.py` with start_fix_nested_tasks_job function
-   [ ] Update `src/main_app/jobs_workers/workers_list.py` to register fix_nested_tasks in jobs_targets_public
-   [ ] Update `src/main_app/jobs_workers/workers_list.py` to add JOB_TYPE_TEMPLATES_PUBLIC entry
-   [ ] Update `src/main_app/jobs_workers/workers_list.py` to add JOB_TYPE_LIST_TEMPLATES_PUBLIC entry
-   [ ] Create `src/templates/jobs_templates/fix_nested_tasks/list.html`
-   [ ] Create `src/templates/jobs_templates/fix_nested_tasks/details.html`
-   [ ] Create unit tests for worker, processor, and service
-   [ ] Create integration tests for routes
-   [ ] Run existing tests to ensure no regressions

## Notes

1. **Reusing Existing Code**: The core fix nested functions in [`fix_nested/worker.py`](src/main_app/app_routes/fix_nested/worker.py:1) should be reused rather than duplicated.

2. **Single File vs Multiple Files**: The public version should support both single file and batch processing. The form should accept either a single filename or a list of filenames.

3. **Authentication**: Users must be logged in to start jobs. OAuth credentials are needed for uploading fixed files.

4. **Result Storage**: Job results should be stored in the same format as other public jobs, using `jobs_service.save_job_result_by_name()`.

5. **Cancellation**: Support job cancellation via the existing `_register_cancel_event` mechanism.

6. **No Database Changes**: This integration does not require any database schema changes. The existing jobs table structure supports new job types.
