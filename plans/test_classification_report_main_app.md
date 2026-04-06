# Test Classification Report — `tests/main_app/`

## Summary Statistics

| Metric                  | Count |
| ----------------------- | ----- |
| Total files analyzed    | 112   |
| MOVE_ONLY → unit        | 108   |
| MOVE_ONLY → integration | 0     |
| MOVE_ONLY → functional  | 0     |
| Files to SPLIT          | 0     |
| Files to DELETE         | 4     |

---

## Files to DELETE

| File                                                                             | Reason                                               |
| -------------------------------------------------------------------------------- | ---------------------------------------------------- |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/test_legacy_worker.py` | Empty TODO stub (only imports + docstring, no tests) |
| `tests/main_app/jobs_workers/test_base_worker.py`                                | Empty TODO stub (only imports, no tests)             |
| `tests/main_app/jobs_workers/test_worker_cancellation.py`                        | Empty TODO stub (only imports, no tests)             |
| `tests/main_app/utils/test_verify.py`                                            | Empty TODO stub (only imports, no tests)             |

---

## Detailed Classification Table

| File                                                                                                  | Type | Action    | Tests Count | Destination                                                                                                |
| ----------------------------------------------------------------------------------------------------- | ---- | --------- | ----------- | ---------------------------------------------------------------------------------------------------------- |
| `tests/main_app/admins/test_admins_required.py`                                                       | unit | MOVE_ONLY | 6           | `tests/unit/main_app/admins/test_admins_required.py`                                                       |
| `tests/main_app/api_services/clients/test_commons_client.py`                                          | unit | MOVE_ONLY | 10          | `tests/unit/main_app/api_services/clients/test_commons_client.py`                                          |
| `tests/main_app/api_services/clients/test_wiki_client.py`                                             | unit | MOVE_ONLY | 1           | `tests/unit/main_app/api_services/clients/test_wiki_client.py`                                             |
| `tests/main_app/api_services/mwclient_page/test_mwclient_page.py`                                     | unit | MOVE_ONLY | 21          | `tests/unit/main_app/api_services/mwclient_page/test_mwclient_page.py`                                     |
| `tests/main_app/api_services/mwclient_page/test_mwclient_page2.py`                                    | unit | MOVE_ONLY | 8           | `tests/unit/main_app/api_services/mwclient_page/test_mwclient_page2.py`                                    |
| `tests/main_app/api_services/test_category.py`                                                        | unit | MOVE_ONLY | 12          | `tests/unit/main_app/api_services/test_category.py`                                                        |
| `tests/main_app/api_services/test_pages_api.py`                                                       | unit | MOVE_ONLY | 22          | `tests/unit/main_app/api_services/test_pages_api.py`                                                       |
| `tests/main_app/api_services/test_text_api.py`                                                        | unit | MOVE_ONLY | 15          | `tests/unit/main_app/api_services/test_text_api.py`                                                        |
| `tests/main_app/api_services/test_text_bot.py`                                                        | unit | MOVE_ONLY | 8           | `tests/unit/main_app/api_services/test_text_bot.py`                                                        |
| `tests/main_app/api_services/test_upload_bot.py`                                                      | unit | MOVE_ONLY | 15          | `tests/unit/main_app/api_services/test_upload_bot.py`                                                      |
| `tests/main_app/api_services/test_upload_bot_new.py`                                                  | unit | MOVE_ONLY | 7           | `tests/unit/main_app/api_services/test_upload_bot_new.py`                                                  |
| `tests/main_app/app_routes/admin/admin_routes/test_coordinators_exception_handling.py`                | unit | MOVE_ONLY | 1           | `tests/unit/main_app/app_routes/admin/admin_routes/test_coordinators_exception_handling.py`                |
| `tests/main_app/app_routes/admin/test_sidebar.py`                                                     | unit | MOVE_ONLY | 13          | `tests/unit/main_app/app_routes/admin/test_sidebar.py`                                                     |
| `tests/main_app/app_routes/auth/test_auth_cookie.py`                                                  | unit | MOVE_ONLY | 4           | `tests/unit/main_app/app_routes/auth/test_auth_cookie.py`                                                  |
| `tests/main_app/app_routes/auth/test_auth_oauth_helpers.py`                                           | unit | MOVE_ONLY | 3           | `tests/unit/main_app/app_routes/auth/test_auth_oauth_helpers.py`                                           |
| `tests/main_app/app_routes/auth/test_cookie.py`                                                       | unit | MOVE_ONLY | 8           | `tests/unit/main_app/app_routes/auth/test_cookie.py`                                                       |
| `tests/main_app/app_routes/auth/test_oauth.py`                                                        | unit | MOVE_ONLY | 7           | `tests/unit/main_app/app_routes/auth/test_oauth.py`                                                        |
| `tests/main_app/app_routes/auth/test_rate_limit.py`                                                   | unit | MOVE_ONLY | 3           | `tests/unit/main_app/app_routes/auth/test_rate_limit.py`                                                   |
| `tests/main_app/app_routes/fix_nested/test_explorer_routes_undo.py`                                   | unit | MOVE_ONLY | 2           | `tests/unit/main_app/app_routes/fix_nested/test_explorer_routes_undo.py`                                   |
| `tests/main_app/app_routes/fix_nested/test_fix_nested_routes_unit.py`                                 | unit | MOVE_ONLY | 3           | `tests/unit/main_app/app_routes/fix_nested/test_fix_nested_routes_unit.py`                                 |
| `tests/main_app/app_routes/fix_nested/test_fix_nested_worker.py`                                      | unit | MOVE_ONLY | 17          | `tests/unit/main_app/app_routes/fix_nested/test_fix_nested_worker.py`                                      |
| `tests/main_app/app_routes/utils/test_args_utils.py`                                                  | unit | MOVE_ONLY | 13          | `tests/unit/main_app/app_routes/utils/test_args_utils.py`                                                  |
| `tests/main_app/app_routes/utils/test_compare.py`                                                     | unit | MOVE_ONLY | 3           | `tests/unit/main_app/app_routes/utils/test_compare.py`                                                     |
| `tests/main_app/app_routes/utils/test_explorer_utils.py`                                              | unit | MOVE_ONLY | 7           | `tests/unit/main_app/app_routes/utils/test_explorer_utils.py`                                              |
| `tests/main_app/app_routes/utils/test_fix_nested_utils.py`                                            | unit | MOVE_ONLY | 10          | `tests/unit/main_app/app_routes/utils/test_fix_nested_utils.py`                                            |
| `tests/main_app/app_routes/utils/test_routes_utils_unit.py`                                           | unit | MOVE_ONLY | 4           | `tests/unit/main_app/app_routes/utils/test_routes_utils_unit.py`                                           |
| `tests/main_app/app_routes/utils/test_thumbnail_utils.py`                                             | unit | MOVE_ONLY | 1           | `tests/unit/main_app/app_routes/utils/test_thumbnail_utils.py`                                             |
| `tests/main_app/core/test_crypto.py`                                                                  | unit | MOVE_ONLY | 1           | `tests/unit/main_app/core/test_crypto.py`                                                                  |
| `tests/main_app/db/test_db_class.py`                                                                  | unit | MOVE_ONLY | 8           | `tests/unit/main_app/db/test_db_class.py`                                                                  |
| `tests/main_app/db/test_db_CoordinatorsDB.py`                                                         | unit | MOVE_ONLY | 23          | `tests/unit/main_app/db/test_db_CoordinatorsDB.py`                                                         |
| `tests/main_app/db/test_db_Jobs.py`                                                                   | unit | MOVE_ONLY | 23          | `tests/unit/main_app/db/test_db_Jobs.py`                                                                   |
| `tests/main_app/db/test_db_OwidCharts.py`                                                             | unit | MOVE_ONLY | 17          | `tests/unit/main_app/db/test_db_OwidCharts.py`                                                             |
| `tests/main_app/db/test_db_Settings.py`                                                               | unit | MOVE_ONLY | 29          | `tests/unit/main_app/db/test_db_Settings.py`                                                               |
| `tests/main_app/db/test_db_Templates.py`                                                              | unit | MOVE_ONLY | 18          | `tests/unit/main_app/db/test_db_Templates.py`                                                              |
| `tests/main_app/db/test_exceptions.py`                                                                | unit | MOVE_ONLY | 5           | `tests/unit/main_app/db/test_exceptions.py`                                                                |
| `tests/main_app/db/test_fix_nested_task_store.py`                                                     | unit | MOVE_ONLY | 8           | `tests/unit/main_app/db/test_fix_nested_task_store.py`                                                     |
| `tests/main_app/db/test_svg_db.py`                                                                    | unit | MOVE_ONLY | 13          | `tests/unit/main_app/db/test_svg_db.py`                                                                    |
| `tests/main_app/jobs_workers/add_svglanguages_template/test_add_svglanguages_template_worker.py`      | unit | MOVE_ONLY | 31          | `tests/unit/main_app/jobs_workers/add_svglanguages_template/test_add_svglanguages_template_worker.py`      |
| `tests/main_app/jobs_workers/create_owid_pages/test_create_owid_pages_worker.py`                      | unit | MOVE_ONLY | 34          | `tests/unit/main_app/jobs_workers/create_owid_pages/test_create_owid_pages_worker.py`                      |
| `tests/main_app/jobs_workers/create_owid_pages/test_owid_template_converter.py`                       | unit | MOVE_ONLY | 4           | `tests/unit/main_app/jobs_workers/create_owid_pages/test_owid_template_converter.py`                       |
| `tests/main_app/jobs_workers/crop_main_files/test_crop_file.py`                                       | unit | MOVE_ONLY | 12          | `tests/unit/main_app/jobs_workers/crop_main_files/test_crop_file.py`                                       |
| `tests/main_app/jobs_workers/crop_main_files/test_crop_main_files_worker.py`                          | unit | MOVE_ONLY | 23          | `tests/unit/main_app/jobs_workers/crop_main_files/test_crop_main_files_worker.py`                          |
| `tests/main_app/jobs_workers/crop_main_files/test_download.py`                                        | unit | MOVE_ONLY | 8           | `tests/unit/main_app/jobs_workers/crop_main_files/test_download.py`                                        |
| `tests/main_app/jobs_workers/crop_main_files/test_process_new.py`                                     | unit | MOVE_ONLY | 13          | `tests/unit/main_app/jobs_workers/crop_main_files/test_process_new.py`                                     |
| `tests/main_app/jobs_workers/crop_main_files/test_upload.py`                                          | unit | MOVE_ONLY | 3           | `tests/unit/main_app/jobs_workers/crop_main_files/test_upload.py`                                          |
| `tests/main_app/jobs_workers/test_base_worker.py`                                                     | —    | DELETE    | 0           | —                                                                                                          |
| `tests/main_app/jobs_workers/test_collect_main_files_worker.py`                                       | unit | MOVE_ONLY | 9           | `tests/unit/main_app/jobs_workers/test_collect_main_files_worker.py`                                       |
| `tests/main_app/jobs_workers/test_download_main_files_worker.py`                                      | unit | MOVE_ONLY | 9           | `tests/unit/main_app/jobs_workers/test_download_main_files_worker.py`                                      |
| `tests/main_app/jobs_workers/test_fix_nested_main_files_worker.py`                                    | unit | MOVE_ONLY | 10          | `tests/unit/main_app/jobs_workers/test_fix_nested_main_files_worker.py`                                    |
| `tests/main_app/jobs_workers/test_jobs_worker.py`                                                     | unit | MOVE_ONLY | 15          | `tests/unit/main_app/jobs_workers/test_jobs_worker.py`                                                     |
| `tests/main_app/jobs_workers/test_worker_cancellation.py`                                             | —    | DELETE    | 0           | —                                                                                                          |
| `tests/main_app/jobs_workers/utils/test_add_svglanguages_template_utils.py`                           | unit | MOVE_ONLY | 8           | `tests/unit/main_app/jobs_workers/utils/test_add_svglanguages_template_utils.py`                           |
| `tests/main_app/jobs_workers/utils/test_crop_main_files_utils.py`                                     | unit | MOVE_ONLY | 11          | `tests/unit/main_app/jobs_workers/utils/test_crop_main_files_utils.py`                                     |
| `tests/main_app/jobs_workers/utils/test_jobs_workers_utils.py`                                        | unit | MOVE_ONLY | 10          | `tests/unit/main_app/jobs_workers/utils/test_jobs_workers_utils.py`                                        |
| `tests/main_app/public_jobs_workers/copy_svg_langs/test_copy_svg_langs_processor.py`                  | unit | MOVE_ONLY | 5           | `tests/unit/main_app/public_jobs_workers/copy_svg_langs/test_copy_svg_langs_processor.py`                  |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_extracts_task.py`                | unit | MOVE_ONLY | 1           | `tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_extracts_task.py`                |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_fix_nested_tasks.py`             | unit | MOVE_ONLY | 2           | `tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_fix_nested_tasks.py`             |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_inject_tasks.py`                 | unit | MOVE_ONLY | 2           | `tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_inject_tasks.py`                 |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_start_bot.py`                    | unit | MOVE_ONLY | 2           | `tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_start_bot.py`                    |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_bot.py`                   | unit | MOVE_ONLY | 2           | `tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_bot.py`                   |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_tasks.py`                 | unit | MOVE_ONLY | 4           | `tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_tasks.py`                 |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_up.py`                           | unit | MOVE_ONLY | 3           | `tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_up.py`                           |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/test_legacy_threads.py`                     | unit | MOVE_ONLY | 1           | `tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/test_legacy_threads.py`                     |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/test_legacy_worker.py`                      | —    | DELETE    | 0           | —                                                                                                          |
| `tests/main_app/services/test_admin_service.py`                                                       | unit | MOVE_ONLY | 7           | `tests/unit/main_app/services/test_admin_service.py`                                                       |
| `tests/main_app/services/test_jobs_service.py`                                                        | unit | MOVE_ONLY | 22          | `tests/unit/main_app/services/test_jobs_service.py`                                                        |
| `tests/main_app/services/test_owid_charts_service.py`                                                 | unit | MOVE_ONLY | 17          | `tests/unit/main_app/services/test_owid_charts_service.py`                                                 |
| `tests/main_app/services/test_template_service.py`                                                    | unit | MOVE_ONLY | 22          | `tests/unit/main_app/services/test_template_service.py`                                                    |
| `tests/main_app/users/test_current_unit.py`                                                           | unit | MOVE_ONLY | 4           | `tests/unit/main_app/users/test_current_unit.py`                                                           |
| `tests/main_app/users/test_store.py`                                                                  | unit | MOVE_ONLY | 19          | `tests/unit/main_app/users/test_store.py`                                                                  |
| `tests/main_app/users/test_users_store.py`                                                            | unit | MOVE_ONLY | 4           | `tests/unit/main_app/users/test_users_store.py`                                                            |
| `tests/main_app/utils/api_services_utils/test_download_file_utils.py`                                 | unit | MOVE_ONLY | 10          | `tests/unit/main_app/utils/api_services_utils/test_download_file_utils.py`                                 |
| `tests/main_app/utils/categories_utils/test_capitalize_category.py`                                   | unit | MOVE_ONLY | 4           | `tests/unit/main_app/utils/categories_utils/test_capitalize_category.py`                                   |
| `tests/main_app/utils/categories_utils/test_categories_utils.py`                                      | unit | MOVE_ONLY | 4           | `tests/unit/main_app/utils/categories_utils/test_categories_utils.py`                                      |
| `tests/main_app/utils/categories_utils/test_extract_categories.py`                                    | unit | MOVE_ONLY | 7           | `tests/unit/main_app/utils/categories_utils/test_extract_categories.py`                                    |
| `tests/main_app/utils/categories_utils/test_find_missing_categories.py`                               | unit | MOVE_ONLY | 9           | `tests/unit/main_app/utils/categories_utils/test_find_missing_categories.py`                               |
| `tests/main_app/utils/categories_utils/test_merge_categories.py`                                      | unit | MOVE_ONLY | 8           | `tests/unit/main_app/utils/categories_utils/test_merge_categories.py`                                      |
| `tests/main_app/utils/test_jinja_filters.py`                                                          | unit | MOVE_ONLY | 6           | `tests/unit/main_app/utils/test_jinja_filters.py`                                                          |
| `tests/main_app/utils/test_verify.py`                                                                 | —    | DELETE    | 0           | —                                                                                                          |
| `tests/main_app/utils/wikitext/temps_bot/test_get_files_list.py`                                      | unit | MOVE_ONLY | 4           | `tests/unit/main_app/utils/wikitext/temps_bot/test_get_files_list.py`                                      |
| `tests/main_app/utils/wikitext/temps_bot/test_get_titles.py`                                          | unit | MOVE_ONLY | 5           | `tests/unit/main_app/utils/wikitext/temps_bot/test_get_titles.py`                                          |
| `tests/main_app/utils/wikitext/temps_bot/test_temps_bot.py`                                           | unit | MOVE_ONLY | 10          | `tests/unit/main_app/utils/wikitext/temps_bot/test_temps_bot.py`                                           |
| `tests/main_app/utils/wikitext/test_appendImageExtractedTemplate.py`                                  | unit | MOVE_ONLY | 3           | `tests/unit/main_app/utils/wikitext/test_appendImageExtractedTemplate.py`                                  |
| `tests/main_app/utils/wikitext/test_before_methods.py`                                                | unit | MOVE_ONLY | 3           | `tests/unit/main_app/utils/wikitext/test_before_methods.py`                                                |
| `tests/main_app/utils/wikitext/test_files_text.py`                                                    | unit | MOVE_ONLY | 11          | `tests/unit/main_app/utils/wikitext/test_files_text.py`                                                    |
| `tests/main_app/utils/wikitext/test_other_versions.py`                                                | unit | MOVE_ONLY | 4           | `tests/unit/main_app/utils/wikitext/test_other_versions.py`                                                |
| `tests/main_app/utils/wikitext/test_temp_source.py`                                                   | unit | MOVE_ONLY | 11          | `tests/unit/main_app/utils/wikitext/test_temp_source.py`                                                   |
| `tests/main_app/utils/wikitext/test_template_page.py`                                                 | unit | MOVE_ONLY | 5           | `tests/unit/main_app/utils/wikitext/test_template_page.py`                                                 |
| `tests/main_app/utils/wikitext/test_text_utils.py`                                                    | unit | MOVE_ONLY | 3           | `tests/unit/main_app/utils/wikitext/test_text_utils.py`                                                    |
| `tests/main_app/utils/wikitext/test_update_original_file_text.py`                                     | unit | MOVE_ONLY | 18          | `tests/unit/main_app/utils/wikitext/test_update_original_file_text.py`                                     |
| `tests/main_app/utils/wikitext/test_update_template_page_file_reference.py`                           | unit | MOVE_ONLY | 5           | `tests/unit/main_app/utils/wikitext/test_update_template_page_file_reference.py`                           |
| `tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py`            | unit | MOVE_ONLY | 11          | `tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py`            |
| `tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py`           | unit | MOVE_ONLY | 9           | `tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py`           |
| `tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py` | unit | MOVE_ONLY | 37          | `tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py` |
| `tests/main_app/utils/wikitext/titles_utils/test_find_main_title.py`                                  | unit | MOVE_ONLY | 9           | `tests/unit/main_app/utils/wikitext/titles_utils/test_find_main_title.py`                                  |
| `tests/main_app/utils/wikitext/titles_utils/test_last_world_file_with_full_date.py`                   | unit | MOVE_ONLY | 11          | `tests/unit/main_app/utils/wikitext/titles_utils/test_last_world_file_with_full_date.py`                   |
| `tests/main_app/utils/wikitext/titles_utils/test_main_file.py`                                        | unit | MOVE_ONLY | 11          | `tests/unit/main_app/utils/wikitext/titles_utils/test_main_file.py`                                        |
| `tests/main_app/utils/wikitext/titles_utils/test_match_main_title.py`                                 | unit | MOVE_ONLY | 9           | `tests/unit/main_app/utils/wikitext/titles_utils/test_match_main_title.py`                                 |
| `tests/main_app/test_init.py`                                                                         | unit | MOVE_ONLY | 9           | `tests/unit/main_app/test_init.py`                                                                         |
| `tests/main_app/test_app_factory.py`                                                                  | unit | MOVE_ONLY | 10          | `tests/unit/main_app/test_app_factory.py`                                                                  |
| `tests/main_app/test_config.py`                                                                       | unit | MOVE_ONLY | 15          | `tests/unit/main_app/test_config.py`                                                                       |
| `tests/main_app/test_data.py`                                                                         | unit | MOVE_ONLY | 1           | `tests/unit/main_app/test_data.py`                                                                         |

---

## Classification Rationale

### Why all files are classified as `unit`

All 108 non-deleted files in `tests/main_app/` use one or more of these patterns that indicate isolation/unit testing:

1. **`@patch` / `MagicMock`** — Used in virtually every file to mock DB connections, HTTP calls, mwclient, file I/O, and external services. No real network or database calls occur.

2. **`monkeypatch`** — Used to replace module-level objects, settings, and paths without touching the real filesystem or network.

3. **Fixtures with mocked dependencies** — DB classes are mocked via `mocker.patch("...Database")` and fixtures create isolated instances.

4. **No `app.test_client()` for route testing** — None of the files test full HTTP request/response cycles through real Flask routes. Files like `test_init.py` and `test_app_factory.py` create a real Flask app but do not exercise the full application stack (no DB, no routing, no real HTTP).

5. **No real database** — Files that test DB-layer code (e.g., `test_db_Jobs.py`, `test_db_CoordinatorsDB.py`) mock the entire `Database` class. No real MySQL/SQLite is used.

### Files deleted (empty stubs/TODOs)

| File                          | Notes                                       |
| ----------------------------- | ------------------------------------------- |
| `test_legacy_worker.py`       | Only imports + docstring, no test functions |
| `test_base_worker.py`         | Only imports + docstring, no test functions |
| `test_worker_cancellation.py` | Only imports + docstring, no test functions |
| `test_verify.py`              | Only imports + docstring, no test functions |

---

## Git Commands

```bash
# ── Move all unit files ──────────────────────────────────────────────────────

# admins
git mv tests/main_app/admins/test_admins_required.py tests/unit/main_app/admins/test_admins_required.py

# api_services/clients
git mv tests/main_app/api_services/clients/test_commons_client.py tests/unit/main_app/api_services/clients/test_commons_client.py
git mv tests/main_app/api_services/clients/test_wiki_client.py tests/unit/main_app/api_services/clients/test_wiki_client.py

# api_services/mwclient_page
git mv tests/main_app/api_services/mwclient_page/test_mwclient_page.py tests/unit/main_app/api_services/mwclient_page/test_mwclient_page.py
git mv tests/main_app/api_services/mwclient_page/test_mwclient_page2.py tests/unit/main_app/api_services/mwclient_page/test_mwclient_page2.py

# api_services (root)
git mv tests/main_app/api_services/test_category.py tests/unit/main_app/api_services/test_category.py
git mv tests/main_app/api_services/test_pages_api.py tests/unit/main_app/api_services/test_pages_api.py
git mv tests/main_app/api_services/test_text_api.py tests/unit/main_app/api_services/test_text_api.py
git mv tests/main_app/api_services/test_text_bot.py tests/unit/main_app/api_services/test_text_bot.py
git mv tests/main_app/api_services/test_upload_bot.py tests/unit/main_app/api_services/test_upload_bot.py
git mv tests/main_app/api_services/test_upload_bot_new.py tests/unit/main_app/api_services/test_upload_bot_new.py

# app_routes/admin/admin_routes
git mv tests/main_app/app_routes/admin/admin_routes/test_coordinators_exception_handling.py tests/unit/main_app/app_routes/admin/admin_routes/test_coordinators_exception_handling.py

# app_routes/admin
git mv tests/main_app/app_routes/admin/test_sidebar.py tests/unit/main_app/app_routes/admin/test_sidebar.py

# app_routes/auth
git mv tests/main_app/app_routes/auth/test_auth_cookie.py tests/unit/main_app/app_routes/auth/test_auth_cookie.py
git mv tests/main_app/app_routes/auth/test_auth_oauth_helpers.py tests/unit/main_app/app_routes/auth/test_auth_oauth_helpers.py
git mv tests/main_app/app_routes/auth/test_cookie.py tests/unit/main_app/app_routes/auth/test_cookie.py
git mv tests/main_app/app_routes/auth/test_oauth.py tests/unit/main_app/app_routes/auth/test_oauth.py
git mv tests/main_app/app_routes/auth/test_rate_limit.py tests/unit/main_app/app_routes/auth/test_rate_limit.py

# app_routes/fix_nested
git mv tests/main_app/app_routes/fix_nested/test_explorer_routes_undo.py tests/unit/main_app/app_routes/fix_nested/test_explorer_routes_undo.py
git mv tests/main_app/app_routes/fix_nested/test_fix_nested_routes_unit.py tests/unit/main_app/app_routes/fix_nested/test_fix_nested_routes_unit.py
git mv tests/main_app/app_routes/fix_nested/test_fix_nested_worker.py tests/unit/main_app/app_routes/fix_nested/test_fix_nested_worker.py

# app_routes/utils
git mv tests/main_app/app_routes/utils/test_args_utils.py tests/unit/main_app/app_routes/utils/test_args_utils.py
git mv tests/main_app/app_routes/utils/test_compare.py tests/unit/main_app/app_routes/utils/test_compare.py
git mv tests/main_app/app_routes/utils/test_explorer_utils.py tests/unit/main_app/app_routes/utils/test_explorer_utils.py
git mv tests/main_app/app_routes/utils/test_fix_nested_utils.py tests/unit/main_app/app_routes/utils/test_fix_nested_utils.py
git mv tests/main_app/app_routes/utils/test_routes_utils_unit.py tests/unit/main_app/app_routes/utils/test_routes_utils_unit.py
git mv tests/main_app/app_routes/utils/test_thumbnail_utils.py tests/unit/main_app/app_routes/utils/test_thumbnail_utils.py

# core
git mv tests/main_app/core/test_crypto.py tests/unit/main_app/core/test_crypto.py

# db
git mv tests/main_app/db/test_db_class.py tests/unit/main_app/db/test_db_class.py
git mv tests/main_app/db/test_db_CoordinatorsDB.py tests/unit/main_app/db/test_db_CoordinatorsDB.py
git mv tests/main_app/db/test_db_Jobs.py tests/unit/main_app/db/test_db_Jobs.py
git mv tests/main_app/db/test_db_OwidCharts.py tests/unit/main_app/db/test_db_OwidCharts.py
git mv tests/main_app/db/test_db_Settings.py tests/unit/main_app/db/test_db_Settings.py
git mv tests/main_app/db/test_db_Templates.py tests/unit/main_app/db/test_db_Templates.py
git mv tests/main_app/db/test_exceptions.py tests/unit/main_app/db/test_exceptions.py
git mv tests/main_app/db/test_fix_nested_task_store.py tests/unit/main_app/db/test_fix_nested_task_store.py
git mv tests/main_app/db/test_svg_db.py tests/unit/main_app/db/test_svg_db.py

# jobs_workers/add_svglanguages_template
git mv tests/main_app/jobs_workers/add_svglanguages_template/test_add_svglanguages_template_worker.py tests/unit/main_app/jobs_workers/add_svglanguages_template/test_add_svglanguages_template_worker.py

# jobs_workers/create_owid_pages
git mv tests/main_app/jobs_workers/create_owid_pages/test_create_owid_pages_worker.py tests/unit/main_app/jobs_workers/create_owid_pages/test_create_owid_pages_worker.py
git mv tests/main_app/jobs_workers/create_owid_pages/test_owid_template_converter.py tests/unit/main_app/jobs_workers/create_owid_pages/test_owid_template_converter.py

# jobs_workers/crop_main_files
git mv tests/main_app/jobs_workers/crop_main_files/test_crop_file.py tests/unit/main_app/jobs_workers/crop_main_files/test_crop_file.py
git mv tests/main_app/jobs_workers/crop_main_files/test_crop_main_files_worker.py tests/unit/main_app/jobs_workers/crop_main_files/test_crop_main_files_worker.py
git mv tests/main_app/jobs_workers/crop_main_files/test_download.py tests/unit/main_app/jobs_workers/crop_main_files/test_download.py
git mv tests/main_app/jobs_workers/crop_main_files/test_process_new.py tests/unit/main_app/jobs_workers/crop_main_files/test_process_new.py
git mv tests/main_app/jobs_workers/crop_main_files/test_upload.py tests/unit/main_app/jobs_workers/crop_main_files/test_upload.py

# jobs_workers (root)
git mv tests/main_app/jobs_workers/test_collect_main_files_worker.py tests/unit/main_app/jobs_workers/test_collect_main_files_worker.py
git mv tests/main_app/jobs_workers/test_download_main_files_worker.py tests/unit/main_app/jobs_workers/test_download_main_files_worker.py
git mv tests/main_app/jobs_workers/test_fix_nested_main_files_worker.py tests/unit/main_app/jobs_workers/test_fix_nested_main_files_worker.py
git mv tests/main_app/jobs_workers/test_jobs_worker.py tests/unit/main_app/jobs_workers/test_jobs_worker.py

# jobs_workers/utils
git mv tests/main_app/jobs_workers/utils/test_add_svglanguages_template_utils.py tests/unit/main_app/jobs_workers/utils/test_add_svglanguages_template_utils.py
git mv tests/main_app/jobs_workers/utils/test_crop_main_files_utils.py tests/unit/main_app/jobs_workers/utils/test_crop_main_files_utils.py
git mv tests/main_app/jobs_workers/utils/test_jobs_workers_utils.py tests/unit/main_app/jobs_workers/utils/test_jobs_workers_utils.py

# public_jobs_workers/copy_svg_langs
git mv tests/main_app/public_jobs_workers/copy_svg_langs/test_copy_svg_langs_processor.py tests/unit/main_app/public_jobs_workers/copy_svg_langs/test_copy_svg_langs_processor.py

# public_jobs_workers/copy_svg_langs_legacy/steps
git mv tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_extracts_task.py tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_extracts_task.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_fix_nested_tasks.py tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_fix_nested_tasks.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_inject_tasks.py tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_inject_tasks.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_start_bot.py tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_start_bot.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_bot.py tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_bot.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_tasks.py tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_tasks.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_up.py tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_up.py

# public_jobs_workers/copy_svg_langs_legacy (root)
git mv tests/main_app/public_jobs_workers/copy_svg_langs_legacy/test_legacy_threads.py tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/test_legacy_threads.py

# services
git mv tests/main_app/services/test_admin_service.py tests/unit/main_app/services/test_admin_service.py
git mv tests/main_app/services/test_jobs_service.py tests/unit/main_app/services/test_jobs_service.py
git mv tests/main_app/services/test_owid_charts_service.py tests/unit/main_app/services/test_owid_charts_service.py
git mv tests/main_app/services/test_template_service.py tests/unit/main_app/services/test_template_service.py

# users
git mv tests/main_app/users/test_current_unit.py tests/unit/main_app/users/test_current_unit.py
git mv tests/main_app/users/test_store.py tests/unit/main_app/users/test_store.py
git mv tests/main_app/users/test_users_store.py tests/unit/main_app/users/test_users_store.py

# utils/api_services_utils
git mv tests/main_app/utils/api_services_utils/test_download_file_utils.py tests/unit/main_app/utils/api_services_utils/test_download_file_utils.py

# utils/categories_utils
git mv tests/main_app/utils/categories_utils/test_capitalize_category.py tests/unit/main_app/utils/categories_utils/test_capitalize_category.py
git mv tests/main_app/utils/categories_utils/test_categories_utils.py tests/unit/main_app/utils/categories_utils/test_categories_utils.py
git mv tests/main_app/utils/categories_utils/test_extract_categories.py tests/unit/main_app/utils/categories_utils/test_extract_categories.py
git mv tests/main_app/utils/categories_utils/test_find_missing_categories.py tests/unit/main_app/utils/categories_utils/test_find_missing_categories.py
git mv tests/main_app/utils/categories_utils/test_merge_categories.py tests/unit/main_app/utils/categories_utils/test_merge_categories.py

# utils (root)
git mv tests/main_app/utils/test_jinja_filters.py tests/unit/main_app/utils/test_jinja_filters.py

# utils/wikitext/temps_bot
git mv tests/main_app/utils/wikitext/temps_bot/test_get_files_list.py tests/unit/main_app/utils/wikitext/temps_bot/test_get_files_list.py
git mv tests/main_app/utils/wikitext/temps_bot/test_get_titles.py tests/unit/main_app/utils/wikitext/temps_bot/test_get_titles.py
git mv tests/main_app/utils/wikitext/temps_bot/test_temps_bot.py tests/unit/main_app/utils/wikitext/temps_bot/test_temps_bot.py

# utils/wikitext (root)
git mv tests/main_app/utils/wikitext/test_appendImageExtractedTemplate.py tests/unit/main_app/utils/wikitext/test_appendImageExtractedTemplate.py
git mv tests/main_app/utils/wikitext/test_before_methods.py tests/unit/main_app/utils/wikitext/test_before_methods.py
git mv tests/main_app/utils/wikitext/test_files_text.py tests/unit/main_app/utils/wikitext/test_files_text.py
git mv tests/main_app/utils/wikitext/test_other_versions.py tests/unit/main_app/utils/wikitext/test_other_versions.py
git mv tests/main_app/utils/wikitext/test_temp_source.py tests/unit/main_app/utils/wikitext/test_temp_source.py
git mv tests/main_app/utils/wikitext/test_template_page.py tests/unit/main_app/utils/wikitext/test_template_page.py
git mv tests/main_app/utils/wikitext/test_text_utils.py tests/unit/main_app/utils/wikitext/test_text_utils.py
git mv tests/main_app/utils/wikitext/test_update_original_file_text.py tests/unit/main_app/utils/wikitext/test_update_original_file_text.py
git mv tests/main_app/utils/wikitext/test_update_template_page_file_reference.py tests/unit/main_app/utils/wikitext/test_update_template_page_file_reference.py

# utils/wikitext/titles_utils/last_world_file_utils
git mv tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py
git mv tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py
git mv tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py

# utils/wikitext/titles_utils
git mv tests/main_app/utils/wikitext/titles_utils/test_find_main_title.py tests/unit/main_app/utils/wikitext/titles_utils/test_find_main_title.py
git mv tests/main_app/utils/wikitext/titles_utils/test_last_world_file_with_full_date.py tests/unit/main_app/utils/wikitext/titles_utils/test_last_world_file_with_full_date.py
git mv tests/main_app/utils/wikitext/titles_utils/test_main_file.py tests/unit/main_app/utils/wikitext/titles_utils/test_main_file.py
git mv tests/main_app/utils/wikitext/titles_utils/test_match_main_title.py tests/unit/main_app/utils/wikitext/titles_utils/test_match_main_title.py

# root tests/main_app/
git mv tests/main_app/test_init.py tests/unit/main_app/test_init.py
git mv tests/main_app/test_app_factory.py tests/unit/main_app/test_app_factory.py
git mv tests/main_app/test_config.py tests/unit/main_app/test_config.py
git mv tests/main_app/test_data.py tests/unit/main_app/test_data.py

# ── Delete empty TODO stubs ──────────────────────────────────────────────────
git rm tests/main_app/jobs_workers/test_base_worker.py
git rm tests/main_app/jobs_workers/test_worker_cancellation.py
git rm tests/main_app/public_jobs_workers/copy_svg_langs_legacy/test_legacy_worker.py
git rm tests/main_app/utils/test_verify.py
```

---

## Full JSON Report

```json
{
    "tests/unit/main_app/admins/test_admins_required.py": {
        "action": "CREATE",
        "source": "tests/main_app/admins/test_admins_required.py",
        "tests": [
            "test_admin_required_redirects_when_not_logged_in",
            "test_admin_required_blocks_non_admin",
            "test_admin_required_allows_admin",
            "test_admin_required_not_logged_in",
            "test_admin_required_not_admin",
            "test_admin_required_is_admin"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/api_services/clients/test_commons_client.py": {
        "action": "CREATE",
        "source": "tests/main_app/api_services/clients/test_commons_client.py",
        "tests": [
            "test_creates_session",
            "test_default_user_agent",
            "test_custom_user_agent",
            "test_successful_download",
            "test_spaces_converted_to_underscores",
            "test_custom_timeout",
            "test_http_error_raises_exception",
            "test_network_error_raises_exception",
            "test_timeout_error_raises_exception",
            "test_filename_is_url_encoded"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/api_services/clients/test_wiki_client.py": {
        "action": "CREATE",
        "source": "tests/main_app/api_services/clients/test_wiki_client.py",
        "tests": ["test_build_upload_site_uses_decrypted_tokens_and_consumer"],
        "type": "unit"
    },
    "tests/unit/main_app/api_services/mwclient_page/test_mwclient_page.py": {
        "action": "CREATE",
        "source": "tests/main_app/api_services/mwclient_page/test_mwclient_page.py",
        "tests": [
            "test_returns_page_on_success",
            "test_caches_page_on_second_call",
            "test_invalid_page_title",
            "test_generic_exception",
            "test_page_exists",
            "test_page_does_not_exist",
            "test_load_page_fails",
            "test_success",
            "test_assert_user_failed",
            "test_user_blocked",
            "test_load_page_fails_invalid_title",
            "test_load_page_fails_generic",
            "test_ratelimited",
            "test_ratelimited_then_success",
            "test_ratelimited_exhausts_all_retries",
            "test_ratelimited_then_other_api_error",
            "test_edit_error_no_retry",
            "test_retry_sleep_delays_are_correct",
            "test_succeeds_on_first_retry",
            "test_returns_ratelimited_after_all_retries",
            "test_stops_early_on_non_ratelimited_error"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/api_services/mwclient_page/test_mwclient_page2.py": {
        "action": "CREATE",
        "source": "tests/main_app/api_services/mwclient_page/test_mwclient_page2.py",
        "tests": [
            "test_edit_error",
            "test_api_error_other",
            "test_generic_exception",
            "test_unexpected_exception",
            "test_protected_page_error",
            "test_protected_page_no_retry",
            "test_ratelimited_then_protected"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/api_services/test_category.py": {
        "action": "CREATE",
        "source": "tests/main_app/api_services/test_category.py",
        "tests": [
            "test_get_category_members_api_success",
            "test_get_category_members_api_no_results",
            "test_get_category_members_api_request_exception",
            "test_get_category_members_api_timeout",
            "test_get_category_members_api_http_error",
            "test_get_category_members_api_multiple_pages",
            "test_get_category_members_filters_templates",
            "test_get_category_members_custom_category",
            "test_get_category_members_empty_results",
            "test_get_category_members_no_valid_templates",
            "test_get_category_members_case_sensitivity"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/api_services/test_pages_api.py": {
        "action": "CREATE",
        "source": "tests/main_app/api_services/test_pages_api.py",
        "tests": [
            "test_page_exists_returns_true",
            "test_page_not_exists_returns_false",
            "test_page_exists_logs_info",
            "test_page_not_exists_logs_warning",
            "test_create_page_success",
            "test_create_page_without_summary",
            "test_create_page_missing_page_name",
            "test_create_page_missing_wikitext",
            "test_create_page_missing_site",
            "test_create_page_load_page_exception",
            "test_create_page_edit_exception",
            "test_valid_inputs",
            "test_adds_file_prefix",
            "test_missing_original_file_returns_error",
            "test_missing_updated_file_text_returns_error",
            "test_missing_site_returns_error",
            "test_empty_original_file_returns_error",
            "test_empty_updated_file_text_returns_error",
            "test_multiple_missing_fields_returns_error",
            "test_with_prefixed_original_file",
            "test_error_message_format",
            "test_valid_inputs_calls_edit",
            "test_missing_page_name_returns_error",
            "test_missing_updated_text_returns_error",
            "test_missing_site_returns_error",
            "test_edit_exception_returns_error",
            "test_default_empty_summary"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/api_services/test_text_api.py": {
        "action": "CREATE",
        "source": "tests/main_app/api_services/test_text_api.py",
        "tests": [
            "test_valid_inputs_returns_text",
            "test_adds_file_prefix",
            "test_missing_file_name_returns_empty_string",
            "test_missing_site_returns_empty_string",
            "test_empty_file_name_returns_empty_string",
            "test_both_missing_returns_empty_string",
            "test_with_prefixed_filename"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/api_services/test_text_bot.py": {
        "action": "CREATE",
        "source": "tests/main_app/api_services/test_text_bot.py",
        "tests": [
            "test_get_page_text",
            "test_get_page_text_empty_title",
            "test_get_page_text_none_site",
            "test_get_wikitext",
            "test_get_wikitext_none_title",
            "test_get_wikitext_none_site",
            "test_get_wikitext_with_prefix",
            "test_ensure_file_prefix"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/api_services/test_upload_bot.py": {
        "action": "CREATE",
        "source": "tests/main_app/api_services/test_upload_bot.py",
        "tests": [
            "test_ensure_file_prefix",
            "test_ensure_file_prefix_already_has_prefix",
            "test_upload_file_success",
            "test_upload_file_returns_success_on_result",
            "test_upload_file_missing_title",
            "test_upload_file_missing_wikitext",
            "test_upload_file_none_site",
            "test_upload_file_failed_upload"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/api_services/test_upload_bot_new.py": {
        "action": "CREATE",
        "source": "tests/main_app/api_services/test_upload_bot_new.py",
        "tests": [
            "test_upload_file_new",
            "test_upload_file_new_success",
            "test_upload_file_new_failure",
            "test_upload_file_new_error_result"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/app_routes/admin/admin_routes/test_coordinators_exception_handling.py": {
        "action": "CREATE",
        "source": "tests/main_app/app_routes/admin/admin_routes/test_coordinators_exception_handling.py",
        "tests": ["test_add_coordinator_catches_both_lookup_and_value_errors"],
        "type": "unit"
    },
    "tests/unit/main_app/app_routes/admin/test_sidebar.py": {
        "action": "CREATE",
        "source": "tests/main_app/app_routes/admin/test_sidebar.py",
        "tests": [
            "test_generate_list_item",
            "test_create_side_marks_active_item",
            "test_generate_list_item_basic",
            "test_generate_list_item_with_icon",
            "test_generate_list_item_with_target",
            "test_generate_list_item_with_icon_and_target",
            "test_create_side_with_active_item",
            "test_sidebar_contains_jobs_section",
            "test_sidebar_contains_collect_main_files_job_link",
            "test_sidebar_contains_fix_nested_main_files_job_link",
            "test_sidebar_marks_collect_main_files_as_active",
            "test_sidebar_marks_fix_nested_main_files_as_active"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/app_routes/auth/test_auth_cookie.py": {
        "action": "CREATE",
        "source": "tests/main_app/app_routes/auth/test_auth_cookie.py",
        "tests": [
            "test_sign_and_extract_roundtrip",
            "test_extract_user_id_tampered_returns_none",
            "test_state_token_roundtrip",
            "test_state_token_invalid_returns_none"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/app_routes/auth/test_auth_oauth_helpers.py": {
        "action": "CREATE",
        "source": "tests/main_app/app_routes/auth/test_auth_oauth_helpers.py",
        "tests": [
            "test_start_login_returns_redirect_and_request_token",
            "test_complete_login_returns_access_and_identity",
            "test_complete_login_raises_identity_error"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/app_routes/auth/test_cookie.py": {
        "action": "CREATE",
        "source": "tests/main_app/app_routes/auth/test_cookie.py",
        "tests": [
            "test_sign_user_id",
            "test_extract_user_id_valid_token",
            "test_extract_user_id_invalid_token",
            "test_sign_state_token",
            "test_verify_state_token_success",
            "test_verify_state_token_invalid_payload",
            "test_verify_state_token_bad_signature"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/app_routes/auth/test_oauth.py": {
        "action": "CREATE",
        "source": "tests/main_app/app_routes/auth/test_oauth.py",
        "tests": [
            "test_get_handshaker",
            "test_get_handshaker_without_config",
            "test_start_login",
            "test_complete_login",
            "test_complete_login_identity_error",
            "test_oauthidentityerror"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/app_routes/auth/test_rate_limit.py": {
        "action": "CREATE",
        "source": "tests/main_app/app_routes/auth/test_rate_limit.py",
        "tests": [
            "test_ratelimiter_enforces_limit",
            "test_ratelimiter_tracks_keys_independently",
            "test_rate_limiter_allow_and_try_after"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/app_routes/fix_nested/test_explorer_routes_undo.py": {
        "action": "CREATE",
        "source": "tests/main_app/app_routes/fix_nested/test_explorer_routes_undo.py",
        "tests": [
            "test_user_token_record_has_username_attribute",
            "test_username_access_in_f_string"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/app_routes/fix_nested/test_fix_nested_routes_unit.py": {
        "action": "CREATE",
        "source": "tests/main_app/app_routes/fix_nested/test_fix_nested_routes_unit.py",
        "tests": [
            "test_get_commons_file_url_basic",
            "test_get_commons_file_url_with_spaces",
            "test_get_commons_file_url_with_special_chars"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/app_routes/fix_nested/test_fix_nested_worker.py": {
        "action": "CREATE",
        "source": "tests/main_app/app_routes/fix_nested/test_fix_nested_worker.py",
        "tests": [
            "test_download_svg_file_success",
            "test_detect_nested_tags",
            "test_fix_nested_tags",
            "test_verify_fix",
            "test_upload_fixed_svg_success",
            "test_process_fix_nested_success",
            "test_download_svg_file_failure",
            "test_detect_nested_tags_empty",
            "test_fix_nested_tags_returns_false",
            "test_verify_fix_all_fixed",
            "test_upload_fixed_svg_no_user",
            "test_upload_fixed_svg_no_site",
            "test_upload_fixed_svg_upload_failure",
            "test_process_fix_nested_download_fails",
            "test_process_fix_nested_no_nested_tags",
            "test_process_fix_nested_fix_fails",
            "test_process_fix_nested_no_tags_fixed",
            "test_process_fix_nested_upload_fails"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/app_routes/utils/test_args_utils.py": {
        "action": "CREATE",
        "source": "tests/main_app/app_routes/utils/test_args_utils.py",
        "tests": [
            "test_parse_args_upload_disabled_by_config",
            "test_parse_args_manual_main_title_and_limits",
            "test_parse_args_empty_manual_main_title",
            "test_parse_args_upload_enabled_when_not_disabled",
            "test_parse_args_upload_disabled_explicit_zero",
            "test_parse_args_upload_not_in_form",
            "test_parse_args_manual_main_title_file_prefix_lowercase",
            "test_parse_args_manual_main_title_only_file_colon",
            "test_parse_args_manual_main_title_whitespace_only",
            "test_parse_args_overwrite_not_present",
            "test_parse_args_default_titles_limit",
            "test_parse_args_custom_titles_limit",
            "test_parse_args_disable_uploads_other_string",
            "test_parse_args_ignore_existing_task_not_set"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/app_routes/utils/test_compare.py": {
        "action": "CREATE",
        "source": "tests/main_app/app_routes/utils/test_compare.py",
        "tests": [
            "test_file_langs_extracts_languages",
            "test_analyze_file_reports_languages",
            "test_compare_svg_files_returns_both"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/app_routes/utils/test_explorer_utils.py": {
        "action": "CREATE",
        "source": "tests/main_app/app_routes/utils/test_explorer_utils.py",
        "tests": [
            "test_get_main_data_reads_json",
            "test_get_files_full_path_returns_all_files",
            "test_get_files_filters_svg",
            "test_get_languages_extracts_codes",
            "test_get_informations_compiles_summary"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/app_routes/utils/test_fix_nested_utils.py": {
        "action": "CREATE",
        "source": "tests/main_app/app_routes/utils/test_fix_nested_utils.py",
        "tests": [
            "test_create_task_folder",
            "test_save_metadata",
            "test_log_to_task",
            "test_create_task_folder_idempotent",
            "test_create_task_folder_with_string_path",
            "test_create_task_folder_creates_nested_dirs",
            "test_log_to_task_appends_multiple_messages",
            "test_log_to_task_includes_timestamp",
            "test_save_metadata_with_non_string_values",
            "test_save_metadata_overwrites_existing"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/app_routes/utils/test_routes_utils_unit.py": {
        "action": "CREATE",
        "source": "tests/main_app/app_routes/utils/test_routes_utils_unit.py",
        "tests": [
            "test_get_error_message_known_and_unknown",
            "test_format_timestamp_variants",
            "test_order_stages_and_format_task",
            "test_load_auth_payload_happy_path"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/app_routes/utils/test_thumbnail_utils.py": {
        "action": "CREATE",
        "source": "tests/main_app/app_routes/utils/test_thumbnail_utils.py",
        "tests": ["test_save_thumb_returns_false2"],
        "type": "unit"
    },
    "tests/unit/main_app/core/test_crypto.py": {
        "action": "CREATE",
        "source": "tests/main_app/core/test_crypto.py",
        "tests": ["test_encrypt_decrypt_roundtrip"],
        "type": "unit"
    },
    "tests/unit/main_app/db/test_db_class.py": {
        "action": "CREATE",
        "source": "tests/main_app/db/test_db_class.py",
        "tests": [
            "test_Database_init_basic",
            "test_Database_ensure_connection_new",
            "test_Database_ensure_connection_ping",
            "test_Database_close",
            "test_Database_context_manager",
            "test_Database_execute_query_success",
            "test_Database_fetch_query_success"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/db/test_db_CoordinatorsDB.py": {
        "action": "CREATE",
        "source": "tests/main_app/db/test_db_CoordinatorsDB.py",
        "tests": [
            "test_CoordinatorRecord",
            "test_ensure_table",
            "test_fetch_by_id_success",
            "test_fetch_by_id_not_found",
            "test_fetch_by_username_success",
            "test_fetch_by_username_not_found",
            "test_seed",
            "test_list",
            "test_add_success",
            "test_add_empty_username",
            "test_add_duplicate",
            "test_set_active",
            "test_delete",
            "test_seed_empty_list",
            "test_seed_only_whitespace",
            "test_seed_strips_whitespace",
            "test_row_to_record_with_all_fields",
            "test_row_to_record_is_active_falsy",
            "test_add_with_whitespace_trimmed",
            "test_set_active_deactivate",
            "test_set_active_not_found",
            "test_delete_not_found",
            "test_list_empty"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/db/test_db_Jobs.py": {
        "action": "CREATE",
        "source": "tests/main_app/db/test_db_Jobs.py",
        "tests": [
            "test_JobRecord",
            "test_ensure_table",
            "test_create_success",
            "test_create_failure",
            "test_get_success",
            "test_get_not_found",
            "test_list_all",
            "test_list_filtered",
            "test_delete_success",
            "test_delete_exception",
            "test_update_status_running",
            "test_update_status_completed",
            "test_update_status_generic",
            "test_update_status_not_found",
            "test_update_status_with_result_file_on_running",
            "test_update_status_failed",
            "test_update_status_cancelled",
            "test_list_with_limit",
            "test_row_to_record_with_all_fields"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/db/test_db_OwidCharts.py": {
        "action": "CREATE",
        "source": "tests/main_app/db/test_db_OwidCharts.py",
        "tests": [
            "test_basic_creation",
            "test_template_source_auto_generated",
            "test_optional_fields_default_none",
            "test_init_creates_table",
            "test_fetch_by_id_success",
            "test_fetch_by_id_not_found",
            "test_fetch_by_slug_success",
            "test_fetch_by_slug_not_found",
            "test_list_returns_all_charts",
            "test_list_published_filters_published",
            "test_add_success",
            "test_add_missing_slug_raises_value_error",
            "test_add_missing_title_raises_value_error",
            "test_add_duplicate_slug_raises_value_error",
            "test_update_success",
            "test_update_nonexistent_raises_lookup_error",
            "test_delete_success",
            "test_delete_nonexistent_raises_lookup_error",
            "test_update_chart_data_partial_update",
            "test_update_chart_data_boolean_fields",
            "test_row_to_record_converts_booleans"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/db/test_db_Settings.py": {
        "action": "CREATE",
        "source": "tests/main_app/db/test_db_Settings.py",
        "tests": [
            "test_settings_db_init",
            "test_get_all_parses_boolean_true",
            "test_get_all_parses_boolean_false",
            "test_get_all_parses_integer",
            "test_get_all_parses_integer_invalid",
            "test_get_all_parses_json",
            "test_get_all_parses_json_invalid",
            "test_get_all_parses_string",
            "test_get_all_handles_none",
            "test_get_raw_all",
            "test_get_by_key_found",
            "test_get_by_key_not_found",
            "test_create_setting_success",
            "test_create_setting_failure",
            "test_create_setting_serialize_boolean",
            "test_create_setting_serialize_integer",
            "test_create_setting_serialize_json",
            "test_update_setting_success",
            "test_update_setting_not_found",
            "test_update_setting_failure",
            "test_update_setting_preserves_type",
            "test_update_setting_with_value_type_skips_select",
            "test_update_setting_without_value_type_queries_db",
            "test_update_setting_with_value_type_serializes_correctly"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/db/test_db_Templates.py": {
        "action": "CREATE",
        "source": "tests/main_app/db/test_db_Templates.py",
        "tests": [
            "test_TemplateRecord",
            "test_ensure_table",
            "test_fetch_by_id_success",
            "test_fetch_by_id_not_found",
            "test_fetch_by_title_success",
            "test_list",
            "test_add_success",
            "test_add_duplicate",
            "test_add_empty_title",
            "test_update_success",
            "test_delete_success",
            "test_row_to_record_with_all_fields",
            "test_row_to_record_with_none_main_file",
            "test_fetch_by_title_not_found",
            "test_add_with_whitespace",
            "test_update_not_found",
            "test_delete_not_found",
            "test_list_empty"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/db/test_exceptions.py": {
        "action": "CREATE",
        "source": "tests/main_app/db/test_exceptions.py",
        "tests": [
            "test_db_connection_error",
            "test_db_timeout_error",
            "test_db_query_error"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/db/test_fix_nested_task_store.py": {
        "action": "CREATE",
        "source": "tests/main_app/db/test_fix_nested_task_store.py",
        "tests": [
            "test_load_tasks_returns_empty_when_no_file",
            "test_save_task",
            "test_load_tasks",
            "test_task_exists_true",
            "test_task_exists_false"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/db/test_svg_db.py": {
        "action": "CREATE",
        "source": "tests/main_app/db/test_svg_db.py",
        "tests": [
            "test_svg_db_init_basic",
            "test_svg_db_init_with_config",
            "test_has_db_config_true",
            "test_has_db_config_false",
            "test_has_db_config_no_config",
            "test_has_db_config_empty_credentials"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/jobs_workers/add_svglanguages_template/test_add_svglanguages_template_worker.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/add_svglanguages_template/test_add_svglanguages_template_worker.py",
        "tests": [
            "test_template_info_initialization",
            "test_template_info_steps_initialized",
            "test_template_info_to_dict",
            "test_worker_initialization",
            "test_get_job_type",
            "test_get_initial_result",
            "test_load_templates_filters_owid_templates",
            "test_apply_limits_with_no_limit",
            "test_apply_limits_applies_limit",
            "test_process_template_success_flow",
            "test_process_template_load_step_fails",
            "test_process_template_generate_step_fails",
            "test_load_template_text_success",
            "test_load_template_text_returns_empty_string",
            "test_load_template_text_skips_if_already_has_svglanguages",
            "test_generate_template_text_success",
            "test_generate_template_text_no_translate_link",
            "test_add_template_success",
            "test_add_template_skips_if_identical",
            "test_save_new_text_success",
            "test_save_new_text_failure",
            "test_fail_marks_step_and_file_as_failed",
            "test_skip_step_marks_step_as_skipped",
            "test_append_adds_template_to_result",
            "test_process_success",
            "test_process_fails_without_site",
            "test_process_handles_cancellation",
            "test_function_creates_and_runs_worker"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/jobs_workers/create_owid_pages/test_create_owid_pages_worker.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/create_owid_pages/test_create_owid_pages_worker.py",
        "tests": [
            "test_default_initialization",
            "test_to_dict",
            "test_worker_initialization",
            "test_get_job_type",
            "test_get_initial_result",
            "test_load_templates_filters_owid_prefix",
            "test_load_templates_returns_empty_when_no_owid_templates",
            "test_apply_limits_with_limit_set",
            "test_apply_limits_with_zero_limit",
            "test_apply_limits_with_limit_greater_than_templates",
            "test_step_load_template_text_success",
            "test_step_load_template_text_failure",
            "test_step_create_new_text_success",
            "test_step_create_new_text_exception",
            "test_step_check_exists_and_update_page_not_exists",
            "test_step_check_exists_and_update_page_identical_content",
            "test_step_check_exists_and_update_page_different_content",
            "test_step_check_exists_and_update_update_fails",
            "test_step_create_new_page_success",
            "test_step_create_new_page_failure",
            "test_create_new_page_title_with_owid_prefix",
            "test_create_new_page_title_with_other_prefix",
            "test_fail_updates_status_and_result",
            "test_skip_step_updates_step_status",
            "test_append_adds_to_result",
            "test_process_no_site_authentication",
            "test_process_no_templates",
            "test_process_single_template_success",
            "test_process_single_template_skipped",
            "test_process_multiple_templates_mixed_results",
            "test_process_with_cancellation",
            "test_entry_point_creates_worker_and_runs",
            "test_entry_point_with_cancel_event"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/jobs_workers/create_owid_pages/test_owid_template_converter.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/create_owid_pages/test_owid_template_converter.py",
        "tests": ["test_create_new_text", "test_create_new_text_with_slider"],
        "type": "unit"
    },
    "tests/unit/main_app/jobs_workers/crop_main_files/test_crop_file.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/crop_main_files/test_crop_file.py",
        "tests": [
            "test_crop_file_success",
            "test_crop_file_returns_error_on_exception",
            "test_crop_file_invalid_crop_data",
            "test_get_viewbox_basic",
            "test_get_viewbox_complex"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/jobs_workers/crop_main_files/test_crop_main_files_worker.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/crop_main_files/test_crop_main_files_worker.py",
        "tests": [
            "test_worker_initialization",
            "test_get_job_type",
            "test_get_initial_result",
            "test_download_step_success",
            "test_download_step_failure",
            "test_process_file_success",
            "test_process_file_skip_existing",
            "test_process_file_skip_cancelled",
            "test_upload_step_success",
            "test_upload_step_disabled",
            "test_upload_step_no_files",
            "test_worker_run_success",
            "test_worker_run_failure"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/jobs_workers/crop_main_files/test_download.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/crop_main_files/test_download.py",
        "tests": [
            "test_empty_filename_returns_error",
            "test_filename_without_file_prefix",
            "test_filename_with_file_prefix",
            "test_download_failure",
            "test_existing_file_result",
            "test_download_exception",
            "test_no_session_provided"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/jobs_workers/crop_main_files/test_process_new.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/crop_main_files/test_process_new.py",
        "tests": [
            "test_process_new_step_success",
            "test_process_new_step_failure",
            "test_process_new_step_no_uncropped",
            "test_process_new_step_cancelled",
            "test_get_viewbox_basic",
            "test_get_viewbox_empty",
            "test_get_viewbox_with_units",
            "test_get_viewbox_invalid",
            "test_ensure_viewbox"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/jobs_workers/crop_main_files/test_upload.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/crop_main_files/test_upload.py",
        "tests": ["test_upload_file_success", "test_upload_file_failure"],
        "type": "unit"
    },
    "tests/unit/main_app/jobs_workers/test_collect_main_files_worker.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/test_collect_main_files_worker.py",
        "tests": [
            "test_collect_templates_data_step_success",
            "test_collect_templates_data_step_failure",
            "test_collect_templates_data_step_no_results",
            "test_collect_templates_data_step_empty_category",
            "test_get_category_members_empty",
            "test_filter_valid_templates",
            "test_filter_valid_templates_empty"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/jobs_workers/test_download_main_files_worker.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/test_download_main_files_worker.py",
        "tests": [
            "test_download_step_success",
            "test_download_step_failure",
            "test_download_step_empty_titles",
            "test_get_files_list_data_empty"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/jobs_workers/test_fix_nested_main_files_worker.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/test_fix_nested_main_files_worker.py",
        "tests": [
            "test_fix_nested_step_success",
            "test_fix_nested_step_failure",
            "test_fix_nested_step_no_files",
            "test_fix_nested_step_no_nested_tags",
            "test_fix_nested_step_cancelled",
            "test_detect_nested_tags"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/jobs_workers/test_jobs_worker.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/test_jobs_worker.py",
        "tests": [
            "test_start_worker",
            "test_start_worker_with_cancel_event",
            "test_worker_already_running",
            "test_get_worker_status"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/jobs_workers/utils/test_add_svglanguages_template_utils.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/utils/test_add_svglanguages_template_utils.py",
        "tests": [
            "test_extract_translate_url",
            "test_extract_translate_url_no_match",
            "test_extract_filename_from_url"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/jobs_workers/utils/test_crop_main_files_utils.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/utils/test_crop_main_files_utils.py",
        "tests": [
            "test_get_svg_dimensions_success",
            "test_get_svg_dimensions_file_not_found",
            "test_get_svg_dimensions_invalid_svg",
            "test_calculate_crop_success",
            "test_calculate_crop_invalid_svg"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/jobs_workers/utils/test_jobs_workers_utils.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/utils/test_jobs_workers_utils.py",
        "tests": [
            "test_generate_result_file_name",
            "test_generate_result_file_name_special_chars"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/public_jobs_workers/copy_svg_langs/test_copy_svg_langs_processor.py": {
        "action": "CREATE",
        "source": "tests/main_app/public_jobs_workers/copy_svg_langs/test_copy_svg_langs_processor.py",
        "tests": [
            "test_extract_text_step_success",
            "test_extract_text_step_fail",
            "test_extract_titles_step_success",
            "test_extract_titles_step_manual_title",
            "test_extract_titles_step_limit",
            "test_processor_compute_output_dir",
            "test_processor_run_text_stage_fail",
            "test_processor_files_processed_tracking"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_extracts_task.py": {
        "action": "CREATE",
        "source": "tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_extracts_task.py",
        "tests": ["test_translations_task_stops_on_failure"],
        "type": "unit"
    },
    "tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_fix_nested_tasks.py": {
        "action": "CREATE",
        "source": "tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_fix_nested_tasks.py",
        "tests": [
            "test_fix_nested_task_success",
            "test_fix_nested_task_no_nested"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_inject_tasks.py": {
        "action": "CREATE",
        "source": "tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_inject_tasks.py",
        "tests": ["test_inject_task_success", "test_inject_task_no_dir"],
        "type": "unit"
    },
    "tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_start_bot.py": {
        "action": "CREATE",
        "source": "tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_start_bot.py",
        "tests": ["test_text_task_success", "test_text_task_fail"],
        "type": "unit"
    },
    "tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_bot.py": {
        "action": "CREATE",
        "source": "tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_bot.py",
        "tests": ["test_titles_task_success", "test_titles_task_fail"],
        "type": "unit"
    },
    "tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_tasks.py": {
        "action": "CREATE",
        "source": "tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_tasks.py",
        "tests": [
            "test_titles_task_success",
            "test_titles_task_manual_title",
            "test_titles_task_limit",
            "test_titles_task_fail"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_up.py": {
        "action": "CREATE",
        "source": "tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_up.py",
        "tests": [
            "test_upload_task_disabled",
            "test_upload_task_no_files",
            "test_upload_task_success"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/test_legacy_threads.py": {
        "action": "CREATE",
        "source": "tests/main_app/public_jobs_workers/copy_svg_langs_legacy/test_legacy_threads.py",
        "tests": ["test_get_cancel_event"],
        "type": "unit"
    },
    "tests/unit/main_app/services/test_admin_service.py": {
        "action": "CREATE",
        "source": "tests/main_app/services/test_admin_service.py",
        "tests": [
            "test_get_admins_db_first_call",
            "test_get_admins_db_cached",
            "test_get_admins_db_no_config",
            "test_active_coordinators",
            "test_list_coordinators",
            "test_add_coordinator",
            "test_set_coordinator_active",
            "test_delete_coordinator"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/services/test_jobs_service.py": {
        "action": "CREATE",
        "source": "tests/main_app/services/test_jobs_service.py",
        "tests": [
            "test_create_job",
            "test_create_job_with_username",
            "test_get_job",
            "test_get_nonexistent_job",
            "test_list_jobs",
            "test_list_jobs_with_limit",
            "test_update_job_status",
            "test_update_job_status_with_result_file",
            "test_save_job_result",
            "test_load_job_result",
            "test_load_nonexistent_job_result",
            "test_load_job_result_with_invalid_json",
            "test_delete_job",
            "test_delete_job_with_correct_type",
            "test_delete_job_with_wrong_type",
            "test_delete_nonexistent_job",
            "test_list_jobs_filtered_by_type",
            "test_list_jobs_filtered_with_limit",
            "test_get_jobs_db_no_config",
            "test_get_jobs_db_cached",
            "test_get_jobs_data_dir_not_configured",
            "test_get_jobs_data_dir_creates_directory",
            "test_save_job_result_with_datetime",
            "test_save_job_result_simple",
            "test_update_job_status_nonexistent"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/services/test_owid_charts_service.py": {
        "action": "CREATE",
        "source": "tests/main_app/services/test_owid_charts_service.py",
        "tests": [
            "test_raises_runtime_error_without_db_config",
            "test_raises_runtime_error_on_init_failure",
            "test_returns_initialized_instance",
            "test_returns_all_charts",
            "test_returns_published_charts",
            "test_returns_chart_by_id",
            "test_raises_lookup_error_for_missing",
            "test_returns_chart_by_slug",
            "test_adds_chart_with_defaults",
            "test_adds_chart_with_options",
            "test_updates_chart",
            "test_updates_chart_data",
            "test_deletes_chart"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/services/test_template_service.py": {
        "action": "CREATE",
        "source": "tests/main_app/services/test_template_service.py",
        "tests": [
            "test_list_templates",
            "test_get_template",
            "test_get_template_by_title",
            "test_add_template",
            "test_update_template",
            "test_delete_template"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/users/test_current_unit.py": {
        "action": "CREATE",
        "source": "tests/main_app/users/test_current_unit.py",
        "tests": [
            "test_set_current_user",
            "test_get_current_user",
            "test_clear_current_user"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/users/test_store.py": {
        "action": "CREATE",
        "source": "tests/main_app/users/test_store.py",
        "tests": [
            "test_current_ts_format",
            "test_coerce_bytes_with_bytes",
            "test_coerce_bytes_with_bytearray",
            "test_coerce_bytes_with_memoryview",
            "test_coerce_bytes_with_invalid_type",
            "test_coerce_bytes_with_int",
            "test_coerce_bytes_with_none",
            "test_mark_token_used_success",
            "test_mark_token_used_failure",
            "test_user_token_record_creation",
            "test_user_token_record_with_timestamps",
            "test_decrypted_success",
            "test_decrypted_calls_mark_token_used",
            "test_ensure_table_no_config",
            "test_ensure_table_creates_table",
            "test_upsert_new_token",
            "test_upsert_updates_existing",
            "test_get_user_token_found",
            "test_get_user_token_not_found",
            "test_get_user_token_string_id",
            "test_get_user_token_coerces_bytes",
            "test_delete_user_token",
            "test_delete_user_token_different_id"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/users/test_users_store.py": {
        "action": "CREATE",
        "source": "tests/main_app/users/test_users_store.py",
        "tests": ["test_set_user", "test_get_user", "test_delete_user"],
        "type": "unit"
    },
    "tests/unit/main_app/utils/api_services_utils/test_download_file_utils.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/api_services_utils/test_download_file_utils.py",
        "tests": [
            "test_ensure_file_prefix",
            "test_ensure_file_prefix_already_prefixed",
            "test_download_one_file_success",
            "test_download_one_file_failure",
            "test_download_one_file_skip_existing"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/utils/categories_utils/test_capitalize_category.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/categories_utils/test_capitalize_category.py",
        "tests": [
            "test_capitalize_category_basic",
            "test_capitalize_category_with_prefix"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/utils/categories_utils/test_categories_utils.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/categories_utils/test_categories_utils.py",
        "tests": [
            "test_format_category_name",
            "test_format_category_name_with_prefix"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/utils/categories_utils/test_extract_categories.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/categories_utils/test_extract_categories.py",
        "tests": [
            "test_extract_categories_basic",
            "test_extract_categories_with_prefix",
            "test_extract_categories_empty"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/utils/categories_utils/test_find_missing_categories.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/categories_utils/test_find_missing_categories.py",
        "tests": [
            "test_find_missing_categories_basic",
            "test_find_missing_categories_empty"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/utils/categories_utils/test_merge_categories.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/categories_utils/test_merge_categories.py",
        "tests": [
            "test_merge_categories_basic",
            "test_merge_categories_with_duplicates"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/utils/test_jinja_filters.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/test_jinja_filters.py",
        "tests": [
            "test_format_stage_timestamp_valid",
            "test_format_stage_timestamp_empty",
            "test_format_stage_timestamp_invalid",
            "test_format_stage_timestamp_afternoon"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/utils/wikitext/temps_bot/test_get_files_list.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/temps_bot/test_get_files_list.py",
        "tests": ["test_get_files_list_data"],
        "type": "unit"
    },
    "tests/unit/main_app/utils/wikitext/temps_bot/test_get_titles.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/temps_bot/test_get_titles.py",
        "tests": ["test_get_titles", "test_get_titles_empty"],
        "type": "unit"
    },
    "tests/unit/main_app/utils/wikitext/temps_bot/test_temps_bot.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/temps_bot/test_temps_bot.py",
        "tests": ["test_extract_files_from_temps_bot"],
        "type": "unit"
    },
    "tests/unit/main_app/utils/wikitext/test_appendImageExtractedTemplate.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/test_appendImageExtractedTemplate.py",
        "tests": ["test_append_image_extracted_template"],
        "type": "unit"
    },
    "tests/unit/main_app/utils/wikitext/test_before_methods.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/test_before_methods.py",
        "tests": ["test_before_tag_exists"],
        "type": "unit"
    },
    "tests/unit/main_app/utils/wikitext/test_files_text.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/test_files_text.py",
        "tests": ["test_get_file_titles_from_text"],
        "type": "unit"
    },
    "tests/unit/main_app/utils/wikitext/test_other_versions.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/test_other_versions.py",
        "tests": ["test_get_other_versions_links"],
        "type": "unit"
    },
    "tests/unit/main_app/utils/wikitext/test_temp_source.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/test_temp_source.py",
        "tests": ["test_get_source_url"],
        "type": "unit"
    },
    "tests/unit/main_app/utils/wikitext/test_template_page.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/test_template_page.py",
        "tests": ["test_get_template_page_title"],
        "type": "unit"
    },
    "tests/unit/main_app/utils/wikitext/test_text_utils.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/test_text_utils.py",
        "tests": ["test_extract_after"],
        "type": "unit"
    },
    "tests/unit/main_app/utils/wikitext/test_update_original_file_text.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/test_update_original_file_text.py",
        "tests": ["test_update_original_file_text_basic"],
        "type": "unit"
    },
    "tests/unit/main_app/utils/wikitext/test_update_template_page_file_reference.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/test_update_template_page_file_reference.py",
        "tests": ["test_update_template_page_file_reference"],
        "type": "unit"
    },
    "tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py",
        "tests": [
            "test_get_last_world_file_basic",
            "test_get_last_world_file_with_year",
            "test_get_last_world_file_with_month"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py",
        "tests": ["test_get_last_world_file_with_various_patterns"],
        "type": "unit"
    },
    "tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py",
        "tests": [
            "test_last_world_file_no_files",
            "test_last_world_file_single_file",
            "test_last_world_file_empty_title",
            "test_last_world_file_special_chars"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/utils/wikitext/titles_utils/test_find_main_title.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/titles_utils/test_find_main_title.py",
        "tests": ["test_find_main_title"],
        "type": "unit"
    },
    "tests/unit/main_app/utils/wikitext/titles_utils/test_last_world_file_with_full_date.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/titles_utils/test_last_world_file_with_full_date.py",
        "tests": ["test_get_last_world_file_with_full_date"],
        "type": "unit"
    },
    "tests/unit/main_app/utils/wikitext/titles_utils/test_main_file.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/titles_utils/test_main_file.py",
        "tests": ["test_get_main_file_basic"],
        "type": "unit"
    },
    "tests/unit/main_app/utils/wikitext/titles_utils/test_match_main_title.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/titles_utils/test_match_main_title.py",
        "tests": ["test_match_main_title"],
        "type": "unit"
    },
    "tests/unit/main_app/test_init.py": {
        "action": "CREATE",
        "source": "tests/main_app/test_init.py",
        "tests": [
            "test_create_app_basic",
            "test_create_app_sets_session_cookie_config",
            "test_create_app_jinja_filter_registered",
            "test_create_app_error_handlers",
            "test_create_app_404_handler",
            "test_create_app_url_map_strict_slashes",
            "test_create_app_template_folder",
            "test_create_app_static_folder"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/test_app_factory.py": {
        "action": "CREATE",
        "source": "tests/main_app/test_app_factory.py",
        "tests": [
            "test_create_app_does_not_touch_mysql_when_unconfigured",
            "test_format_stage_timestamp_valid",
            "test_format_stage_timestamp_empty",
            "test_format_stage_timestamp_invalid",
            "test_format_stage_timestamp_afternoon"
        ],
        "type": "unit"
    },
    "tests/unit/main_app/test_config.py": {
        "action": "CREATE",
        "source": "tests/main_app/test_config.py",
        "tests": ["test_load_settings_basic"],
        "type": "unit"
    },
    "tests/unit/main_app/test_data.py": {
        "action": "CREATE",
        "source": "tests/main_app/test_data.py",
        "tests": ["test_get_slug_categories"],
        "type": "unit"
    },
    "tests/main_app/jobs_workers/test_base_worker.py": {
        "action": "DELETE",
        "reason": "Empty TODO stub - no test functions"
    },
    "tests/main_app/jobs_workers/test_worker_cancellation.py": {
        "action": "DELETE",
        "reason": "Empty TODO stub - no test functions"
    },
    "tests/main_app/public_jobs_workers/copy_svg_langs_legacy/test_legacy_worker.py": {
        "action": "DELETE",
        "reason": "Empty TODO stub - no test functions"
    },
    "tests/main_app/utils/test_verify.py": {
        "action": "DELETE",
        "reason": "Empty TODO stub - no test functions"
    }
}
```
