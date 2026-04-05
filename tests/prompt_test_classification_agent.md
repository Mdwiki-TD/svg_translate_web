You are a test classification agent. Your task is to analyze all test files under
`tests/main_app/` and classify them into the new test structure.

## Context

The project is reorganizing tests into three types:

1. **Unit Tests** (`tests/unit/`): Tests a single function/class in isolation

    - Uses mocks/patches for all external dependencies (DB, HTTP, filesystem)
    - No real Flask app context, no real DB connections
    - Fast, no I/O

2. **Integration Tests** (`tests/integration/`): Tests interaction between 2–3 components

    - May use a real in-memory DB (e.g. SQLite fixture) or Flask test client
    - Tests that a service correctly calls the DB layer, or that a route correctly
      calls a service — but not the full user-facing flow

3. **Functional Tests** (`tests/functional/`): Tests a complete user-facing flow end-to-end
    - Uses Flask test client + real routes + real DB together
    - Simulates what a real user/browser would do

## Path Mirroring Rule

Every test file **must mirror** its `src/main_app/` counterpart path. Examples:

-   `src/main_app/db/db_Jobs.py` → `tests/unit/main_app/db/test_db_Jobs.py`
-   `src/main_app/app_routes/auth/routes.py` → `tests/integration/main_app/app_routes/auth/test_routes.py`
-   `src/main_app/services/jobs_service.py` → `tests/unit/main_app/services/test_jobs_service.py`

## Split File Naming Convention

If a file contains tests of two different types (e.g. unit + integration),
it must be split into two files using this naming pattern:

```
test_store.py        ← integration half
test_store_unit.py   ← unit half
```

## Your Task

For **every file** listed in the scope below:

1. **Read the file** and analyze each test function
2. **Classify each test** as `unit`, `integration`, or `functional`
3. **Determine the action**:
    - `MOVE_ONLY` — all tests are the same type, just move the file
    - `SPLIT` — tests are mixed types, file must be split into two files
    - `DELETE` — file is empty or a placeholder (delete after review)
4. **Output a JSON report** with this structure:

```json
{
    "tests/unit/main_app/db/test_db_Jobs.py": {
        "action": "CREATE",
        "source": "tests/main_app/db/test_db_Jobs.py",
        "tests": [
            "test_insert_job_raises_on_missing_field",
            "test_status_enum_values"
        ],
        "type": "unit"
    },
    "tests/integration/main_app/db/test_db_Jobs.py": {
        "action": "CREATE",
        "source": "tests/main_app/db/test_db_Jobs.py",
        "tests": ["test_insert_and_retrieve_job", "test_update_job_status"],
        "type": "integration"
    },
    "tests/main_app/db/test_db_Jobs.py": {
        "action": "DELETE",
        "reason": "Split into unit and integration"
    }
}
```

## Classification Signals

| Signal in test code                                  | Type        |
| ---------------------------------------------------- | ----------- |
| `MagicMock()`, `patch()`, `monkeypatch` on DB/HTTP   | unit        |
| `@pytest.mark.unit`                                  | unit        |
| Tests a single pure function (no I/O)                | unit        |
| Uses a real SQLite fixture or in-memory DB           | integration |
| Uses `app.test_client()` to call a route             | integration |
| Tests service calling DB layer with real objects     | integration |
| Full flow: login → action → DB check via test client | functional  |
| `@pytest.mark.functional`                            | functional  |

## Scope — Files to Analyze

Analyze **only** the following files (read each one before classifying):

### tests/main_app/admins/

-   tests/main_app/admins/test_admins_required.py

### tests/main_app/api_services/

-   tests/main_app/api_services/clients/test_commons_client.py
-   tests/main_app/api_services/clients/test_wiki_client.py
-   tests/main_app/api_services/mwclient_page/test_mwclient_page.py
-   tests/main_app/api_services/mwclient_page/test_mwclient_page2.py
-   tests/main_app/api_services/test_category.py
-   tests/main_app/api_services/test_pages_api.py
-   tests/main_app/api_services/test_text_api.py
-   tests/main_app/api_services/test_text_bot.py
-   tests/main_app/api_services/test_upload_bot.py
-   tests/main_app/api_services/test_upload_bot_new.py

### tests/main_app/app_routes/

-   tests/main_app/app_routes/admin/admin_routes/test_coordinators_exception_handling.py
-   tests/main_app/app_routes/admin/test_sidebar.py
-   tests/main_app/app_routes/auth/test_auth_cookie.py
-   tests/main_app/app_routes/auth/test_auth_oauth_helpers.py
-   tests/main_app/app_routes/auth/test_cookie.py
-   tests/main_app/app_routes/auth/test_oauth.py
-   tests/main_app/app_routes/auth/test_rate_limit.py
-   tests/main_app/app_routes/fix_nested/test_explorer_routes_undo.py
-   tests/main_app/app_routes/fix_nested/test_fix_nested_routes_unit.py
-   tests/main_app/app_routes/fix_nested/test_fix_nested_worker.py
-   tests/main_app/app_routes/utils/test_args_utils.py
-   tests/main_app/app_routes/utils/test_compare.py
-   tests/main_app/app_routes/utils/test_explorer_utils.py
-   tests/main_app/app_routes/utils/test_fix_nested_utils.py
-   tests/main_app/app_routes/utils/test_routes_utils_unit.py
-   tests/main_app/app_routes/utils/test_thumbnail_utils.py

### tests/main_app/core/

-   tests/main_app/core/test_crypto.py

### tests/main_app/db/

-   tests/main_app/db/test_db_class.py
-   tests/main_app/db/test_db_CoordinatorsDB.py
-   tests/main_app/db/test_db_Jobs.py
-   tests/main_app/db/test_db_OwidCharts.py
-   tests/main_app/db/test_db_Settings.py
-   tests/main_app/db/test_db_Templates.py
-   tests/main_app/db/test_exceptions.py
-   tests/main_app/db/test_fix_nested_task_store.py
-   tests/main_app/db/test_svg_db.py

### tests/main_app/jobs_workers/

-   tests/main_app/jobs_workers/add_svglanguages_template/test_add_svglanguages_template_worker.py
-   tests/main_app/jobs_workers/create_owid_pages/test_create_owid_pages_worker.py
-   tests/main_app/jobs_workers/create_owid_pages/test_owid_template_converter.py
-   tests/main_app/jobs_workers/crop_main_files/test_crop_file.py
-   tests/main_app/jobs_workers/crop_main_files/test_crop_main_files_worker.py
-   tests/main_app/jobs_workers/crop_main_files/test_download.py
-   tests/main_app/jobs_workers/crop_main_files/test_process_new.py
-   tests/main_app/jobs_workers/crop_main_files/test_upload.py
-   tests/main_app/jobs_workers/test_base_worker.py
-   tests/main_app/jobs_workers/test_collect_main_files_worker.py
-   tests/main_app/jobs_workers/test_download_main_files_worker.py
-   tests/main_app/jobs_workers/test_fix_nested_main_files_worker.py
-   tests/main_app/jobs_workers/test_jobs_worker.py
-   tests/main_app/jobs_workers/test_worker_cancellation.py
-   tests/main_app/jobs_workers/utils/test_add_svglanguages_template_utils.py
-   tests/main_app/jobs_workers/utils/test_crop_main_files_utils.py
-   tests/main_app/jobs_workers/utils/test_jobs_workers_utils.py

### tests/main_app/public_jobs_workers/

-   tests/main_app/public_jobs_workers/copy_svg_langs/test_copy_svg_langs_processor.py
-   tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_extracts_task.py
-   tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_fix_nested_tasks.py
-   tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_inject_tasks.py
-   tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_start_bot.py
-   tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_bot.py
-   tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_tasks.py
-   tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_up.py
-   tests/main_app/public_jobs_workers/copy_svg_langs_legacy/test_legacy_threads.py
-   tests/main_app/public_jobs_workers/copy_svg_langs_legacy/test_legacy_worker.py

### tests/main_app/services/

-   tests/main_app/services/test_admin_service.py
-   tests/main_app/services/test_jobs_service.py
-   tests/main_app/services/test_owid_charts_service.py
-   tests/main_app/services/test_template_service.py

### tests/main_app/users/

-   tests/main_app/users/test_current_unit.py
-   tests/main_app/users/test_store.py
-   tests/main_app/users/test_users_store.py

### tests/main_app/utils/

-   tests/main_app/utils/api_services_utils/test_download_file_utils.py
-   tests/main_app/utils/categories_utils/test_capitalize_category.py
-   tests/main_app/utils/categories_utils/test_categories_utils.py
-   tests/main_app/utils/categories_utils/test_extract_categories.py
-   tests/main_app/utils/categories_utils/test_find_missing_categories.py
-   tests/main_app/utils/categories_utils/test_merge_categories.py
-   tests/main_app/utils/test_jinja_filters.py
-   tests/main_app/utils/test_verify.py
-   tests/main_app/utils/wikitext/temps_bot/test_get_files_list.py
-   tests/main_app/utils/wikitext/temps_bot/test_get_titles.py
-   tests/main_app/utils/wikitext/temps_bot/test_temps_bot.py
-   tests/main_app/utils/wikitext/test_appendImageExtractedTemplate.py
-   tests/main_app/utils/wikitext/test_before_methods.py
-   tests/main_app/utils/wikitext/test_files_text.py
-   tests/main_app/utils/wikitext/test_other_versions.py
-   tests/main_app/utils/wikitext/test_temp_source.py
-   tests/main_app/utils/wikitext/test_template_page.py
-   tests/main_app/utils/wikitext/test_text_utils.py
-   tests/main_app/utils/wikitext/test_update_original_file_text.py
-   tests/main_app/utils/wikitext/test_update_template_page_file_reference.py
-   tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py
-   tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py
-   tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py
-   tests/main_app/utils/wikitext/titles_utils/test_find_main_title.py
-   tests/main_app/utils/wikitext/titles_utils/test_last_world_file_with_full_date.py
-   tests/main_app/utils/wikitext/titles_utils/test_main_file.py
-   tests/main_app/utils/wikitext/titles_utils/test_match_main_title.py

### tests/main_app/ (root)

-   tests/main_app/test_init.py
-   tests/main_app/test_app_factory.py
-   tests/main_app/test_config.py
-   tests/main_app/test_data.py

## Important Notes

-   **Do NOT skip any file** — read and classify every file listed above
-   **Skip** `conftest.py` files
-   **Skip** files already under `tests/unit/`, `tests/integration/`, `tests/functional/`
-   When a file path under `tests/main_app/users/` has no matching `src/main_app/users/` module,
    trace the import in the test file to find the real source module and mirror that path instead
-   For `SPLIT` files: list which exact test function names go to each destination

## Output Format

Return a Markdown report saved to `plans/test_classification_report_main_app.md` with:

1. **Summary Statistics**

    - Total files analyzed
    - Files MOVE_ONLY → unit
    - Files MOVE_ONLY → integration
    - Files MOVE_ONLY → functional
    - Files to SPLIT
    - Files to DELETE

2. **Detailed Classification Table**

| File                                | Type  | Action | Tests Count | Destination              |
| ----------------------------------- | ----- | ------ | ----------- | ------------------------ |
| `tests/main_app/db/test_db_Jobs.py` | mixed | SPLIT  | 6           | unit(4) + integration(2) |

3. **Files Requiring Split** (detailed breakdown per file)

    - Source file
    - Which test functions → unit destination
    - Which test functions → integration destination

4. **Git Commands** (ready-to-execute)

```bash
# Move files (MOVE_ONLY)
git mv tests/main_app/old/path.py tests/unit/main_app/new/path.py

# Split files — create new files, then delete old
# (list each split file with its two destination paths)
```

5. **Full JSON Report** (the complete JSON described above)

Start by reading the files one by one. Be thorough and accurate.
