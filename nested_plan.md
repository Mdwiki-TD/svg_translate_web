# Implementation Plan: Fix Nested Tags Feature Enhancements

## Overview
The current fix_nested endpoint exists but doesn't:
1. Save task metadata to database
2. Store original files before modification
3. Allow undo/restore functionality
4. Have explorer endpoints similar to main tasks
5. Have before/after comparison endpoints
6. Store files in a dedicated folder with proper structure

---

## Phase 1: Database Schema & Task Storage

- [ ] Create new database table `fix_nested_tasks` with fields:
  - [ ] `id` (VARCHAR 128, primary key)
  - [ ] `username` (TEXT)
  - [ ] `filename` (TEXT) - original filename
  - [ ] `status` (VARCHAR 64) - pending/running/completed/failed/cancelled
  - [ ] `nested_tags_before` (INT) - count before fix
  - [ ] `nested_tags_after` (INT) - count after fix
  - [ ] `nested_tags_fixed` (INT) - count fixed
  - [ ] `download_result` (JSON) - download metadata
  - [ ] `upload_result` (JSON) - upload metadata
  - [ ] `error_message` (TEXT) - if failed
  - [ ] `created_at` (TIMESTAMP)
  - [ ] `updated_at` (TIMESTAMP)

- [ ] Create database helper class `FixNestedTaskStore` (similar to `TaskStorePyMysql`)
  - [ ] Implement CRUD operations
  - [ ] Add methods for listing tasks by status/user

---

## Phase 2: File Storage System

- [ ] Add environment variable `FIX_NESTED_DATA_PATH` to `example.env` (default: `fix_nested_data`)
- [ ] Update `config.py` to load `fix_nested_data_path` from environment
- [ ] Create folder structure for each task:
  ```
  fix_nested_data/
    ├── <task_id>/
    │   ├── original/
    │   │   └── <filename>.svg
    │   ├── fixed/
    │   │   └── <filename>.svg
    │   ├── metadata.json (user, timestamps, results)
    │   └── task_log.txt (detailed logs)
  ```

- [ ] Update `fix_utils.py` to:
  - [ ] Save original file to `original/` folder before fixing
  - [ ] Save fixed file to `fixed/` folder after fixing
  - [ ] Create metadata.json with all task details
  - [ ] Create task_log.txt with detailed processing logs

---

## Phase 3: Task Lifecycle Management

- [ ] Modify `routes.py` to:
  - [ ] Generate unique task_id (UUID) for each fix request
  - [ ] Create task record in database before processing
  - [ ] Update task status throughout processing
  - [ ] Store final results in database

- [ ] Update `process_fix_nested()` to:
  - [ ] Accept task_id parameter
  - [ ] Save files to task-specific folder
  - [ ] Update database at each step
  - [ ] Log all operations to task_log.txt

---

## Phase 4: Undo/Restore Functionality

- [ ] Add new endpoint: `POST /fix_nested/<task_id>/undo`
  - [ ] Verify task exists and was successful
  - [ ] Upload original file back to Commons
  - [ ] Update task status to "undone"
  - [ ] Update upload_result with undo information

- [ ] Update UI to show "Undo" button for completed tasks
- [ ] Add confirmation dialog before undo

---

## Phase 5: Explorer Endpoints

- [ ] Create new blueprint section `fix_nested/explorer/` with routes:
  - [ ] `GET /fix_nested/tasks` - List all fix_nested tasks (with filters)
    - Query parameters: status, username, date_range
    - Show: filename, status, tags_fixed, created_at, actions
  
  - [ ] `GET /fix_nested/tasks/<task_id>` - View single task details
    - Show: all metadata, download/upload results, logs
    - Links to original/fixed files
    - Undo button if applicable
  
  - [ ] `GET /fix_nested/tasks/<task_id>/files/<file_type>` - Serve files
    - file_type: "original" or "fixed"
    - Serve from task folder

---

## Phase 6: Before/After Comparison

- [ ] Add endpoint: `GET /fix_nested/tasks/<task_id>/compare`
  - [ ] Reuse existing `analyze_file()` from explorer/compare.py
  - [ ] Show side-by-side comparison of original vs fixed
  - [ ] Highlight: languages, nested tags count, file size
  - [ ] Render using similar template to main explorer compare

- [ ] Update `analyze_file()` to also show:
  - [ ] Nested tags count and details
  - [ ] File size comparison

---

## Phase 7: Integration & Testing

- [ ] Update main navigation to include link to fix_nested tasks explorer
- [ ] Add rate limiting to prevent abuse
- [ ] Update tests:
  - [ ] Unit tests for database operations
  - [ ] Integration tests for full workflow
  - [ ] Test undo functionality
  - [ ] Test edge cases (file not found, upload fails, etc.)

- [ ] Add migration script if needed for existing data
- [ ] Update documentation

---

## File Changes Summary

### New Files:
- `src/app/db/fix_nested_task_store.py` - Database operations
- `src/app/app_routes/fix_nested/explorer_routes.py` - Explorer endpoints
- `src/app/app_routes/fix_nested/compare.py` - Comparison logic
- `src/templates/fix_nested/tasks_list.html` - Task list UI
- `src/templates/fix_nested/task_detail.html` - Task detail UI
- `src/templates/fix_nested/compare.html` - Comparison UI
- `tests/app/tasks/fix_nested/test_fix_nested_store.py` - Database tests
- `tests/app/app_routes/fix_nested/test_explorer.py` - Explorer tests

### Modified Files:
- `src/example.env` - Add FIX_NESTED_DATA_PATH
- `src/app/config.py` - Load fix_nested_data_path
- `src/app/app_routes/fix_nested/routes.py` - Task lifecycle management
- `src/app/app_routes/fix_nested/fix_utils.py` - File storage logic
- `src/app/app_routes/fix_nested/__init__.py` - Export new blueprints
- `src/app/__init__.py` - Register explorer blueprint
- `src/templates/_navbar.html` - Add explorer link

---

## Implementation Order

1. **Phase 2** (File Storage) - Foundation for storing files
2. **Phase 1** (Database) - Task metadata storage
3. **Phase 3** (Task Lifecycle) - Integrate storage with existing workflow
4. **Phase 5** (Explorer) - View tasks and files
5. **Phase 6** (Comparison) - Compare before/after
6. **Phase 4** (Undo) - Restore functionality
7. **Phase 7** (Testing & Documentation) - Finalize

---

## Key Design Decisions

1. **Separate database table**: Keeps fix_nested tasks isolated from main translation tasks
2. **Task-based folders**: Each fix operation gets unique folder for easy tracking
3. **Metadata.json**: Self-contained task information for backup/debugging
4. **Reuse existing components**: Leverage explorer/compare logic from main tasks
5. **Environment variable**: Configurable storage path for flexibility
