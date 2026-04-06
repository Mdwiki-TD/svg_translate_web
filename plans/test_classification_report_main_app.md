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

| File                                                                                                  | Type | Action    | Tests Count | Destination                                                                                       |
| ----------------------------------------------------------------------------------------------------- | ---- | --------- | ----------- | ------------------------------------------------------------------------------------------------- |
| `tests/main_app/admins/test_admins_required.py`                                                       | unit | MOVE_ONLY | 6           | `tests/unit/admins/test_admins_required.py`                                                       |
| `tests/main_app/api_services/clients/test_commons_client.py`                                          | unit | MOVE_ONLY | 10          | `tests/unit/api_services/clients/test_commons_client.py`                                          |
| `tests/main_app/api_services/clients/test_wiki_client.py`                                             | unit | MOVE_ONLY | 1           | `tests/unit/api_services/clients/test_wiki_client.py`                                             |
| `tests/main_app/api_services/mwclient_page/test_mwclient_page.py`                                     | unit | MOVE_ONLY | 21          | `tests/unit/api_services/mwclient_page/test_mwclient_page.py`                                     |
| `tests/main_app/api_services/mwclient_page/test_mwclient_page2.py`                                    | unit | MOVE_ONLY | 8           | `tests/unit/api_services/mwclient_page/test_mwclient_page2.py`                                    |
| `tests/main_app/api_services/test_category.py`                                                        | unit | MOVE_ONLY | 12          | `tests/unit/api_services/test_category.py`                                                        |
| `tests/main_app/api_services/test_pages_api.py`                                                       | unit | MOVE_ONLY | 22          | `tests/unit/api_services/test_pages_api.py`                                                       |
| `tests/main_app/api_services/test_text_api.py`                                                        | unit | MOVE_ONLY | 15          | `tests/unit/api_services/test_text_api.py`                                                        |
| `tests/main_app/api_services/test_text_bot.py`                                                        | unit | MOVE_ONLY | 8           | `tests/unit/api_services/test_text_bot.py`                                                        |
| `tests/main_app/api_services/test_upload_bot.py`                                                      | unit | MOVE_ONLY | 15          | `tests/unit/api_services/test_upload_bot.py`                                                      |
| `tests/main_app/api_services/test_upload_bot_new.py`                                                  | unit | MOVE_ONLY | 7           | `tests/unit/api_services/test_upload_bot_new.py`                                                  |
| `tests/main_app/app_routes/admin/admin_routes/test_coordinators_exception_handling.py`                | unit | MOVE_ONLY | 1           | `tests/unit/app_routes/admin/admin_routes/test_coordinators_exception_handling.py`                |
| `tests/main_app/app_routes/admin/test_sidebar.py`                                                     | unit | MOVE_ONLY | 13          | `tests/unit/app_routes/admin/test_sidebar.py`                                                     |
| `tests/main_app/app_routes/auth/test_auth_cookie.py`                                                  | unit | MOVE_ONLY | 4           | `tests/unit/app_routes/auth/test_auth_cookie.py`                                                  |
| `tests/main_app/app_routes/auth/test_auth_oauth_helpers.py`                                           | unit | MOVE_ONLY | 3           | `tests/unit/app_routes/auth/test_auth_oauth_helpers.py`                                           |
| `tests/main_app/app_routes/auth/test_cookie.py`                                                       | unit | MOVE_ONLY | 8           | `tests/unit/app_routes/auth/test_cookie.py`                                                       |
| `tests/main_app/app_routes/auth/test_oauth.py`                                                        | unit | MOVE_ONLY | 7           | `tests/unit/app_routes/auth/test_oauth.py`                                                        |
| `tests/main_app/app_routes/auth/test_rate_limit.py`                                                   | unit | MOVE_ONLY | 3           | `tests/unit/app_routes/auth/test_rate_limit.py`                                                   |
| `tests/main_app/app_routes/fix_nested/test_explorer_routes_undo.py`                                   | unit | MOVE_ONLY | 2           | `tests/unit/app_routes/fix_nested/test_explorer_routes_undo.py`                                   |
| `tests/main_app/app_routes/fix_nested/test_fix_nested_routes_unit.py`                                 | unit | MOVE_ONLY | 3           | `tests/unit/app_routes/fix_nested/test_fix_nested_routes_unit.py`                                 |
| `tests/main_app/app_routes/fix_nested/test_fix_nested_worker.py`                                      | unit | MOVE_ONLY | 17          | `tests/unit/app_routes/fix_nested/test_fix_nested_worker.py`                                      |
| `tests/main_app/app_routes/utils/test_args_utils.py`                                                  | unit | MOVE_ONLY | 13          | `tests/unit/app_routes/utils/test_args_utils.py`                                                  |
| `tests/main_app/app_routes/utils/test_compare.py`                                                     | unit | MOVE_ONLY | 3           | `tests/unit/app_routes/utils/test_compare.py`                                                     |
| `tests/main_app/app_routes/utils/test_explorer_utils.py`                                              | unit | MOVE_ONLY | 7           | `tests/unit/app_routes/utils/test_explorer_utils.py`                                              |
| `tests/main_app/app_routes/utils/test_fix_nested_utils.py`                                            | unit | MOVE_ONLY | 10          | `tests/unit/app_routes/utils/test_fix_nested_utils.py`                                            |
| `tests/main_app/app_routes/utils/test_routes_utils_unit.py`                                           | unit | MOVE_ONLY | 4           | `tests/unit/app_routes/utils/test_routes_utils_unit.py`                                           |
| `tests/main_app/app_routes/utils/test_thumbnail_utils.py`                                             | unit | MOVE_ONLY | 1           | `tests/unit/app_routes/utils/test_thumbnail_utils.py`                                             |
| `tests/main_app/core/test_crypto.py`                                                                  | unit | MOVE_ONLY | 1           | `tests/unit/core/test_crypto.py`                                                                  |
| `tests/main_app/db/test_db_class.py`                                                                  | unit | MOVE_ONLY | 8           | `tests/unit/db/test_db_class.py`                                                                  |
| `tests/main_app/db/test_db_CoordinatorsDB.py`                                                         | unit | MOVE_ONLY | 23          | `tests/unit/db/test_db_CoordinatorsDB.py`                                                         |
| `tests/main_app/db/test_db_Jobs.py`                                                                   | unit | MOVE_ONLY | 23          | `tests/unit/db/test_db_Jobs.py`                                                                   |
| `tests/main_app/db/test_db_OwidCharts.py`                                                             | unit | MOVE_ONLY | 17          | `tests/unit/db/test_db_OwidCharts.py`                                                             |
| `tests/main_app/db/test_db_Settings.py`                                                               | unit | MOVE_ONLY | 29          | `tests/unit/db/test_db_Settings.py`                                                               |
| `tests/main_app/db/test_db_Templates.py`                                                              | unit | MOVE_ONLY | 18          | `tests/unit/db/test_db_Templates.py`                                                              |
| `tests/main_app/db/test_exceptions.py`                                                                | unit | MOVE_ONLY | 5           | `tests/unit/db/test_exceptions.py`                                                                |
| `tests/main_app/db/test_fix_nested_task_store.py`                                                     | unit | MOVE_ONLY | 8           | `tests/unit/db/test_fix_nested_task_store.py`                                                     |
| `tests/main_app/db/test_svg_db.py`                                                                    | unit | MOVE_ONLY | 13          | `tests/unit/db/test_svg_db.py`                                                                    |
| `tests/main_app/jobs_workers/add_svglanguages_template/test_add_svglanguages_template_worker.py`      | unit | MOVE_ONLY | 31          | `tests/unit/jobs_workers/add_svglanguages_template/test_add_svglanguages_template_worker.py`      |
| `tests/main_app/jobs_workers/create_owid_pages/test_create_owid_pages_worker.py`                      | unit | MOVE_ONLY | 34          | `tests/unit/jobs_workers/create_owid_pages/test_create_owid_pages_worker.py`                      |
| `tests/main_app/jobs_workers/create_owid_pages/test_owid_template_converter.py`                       | unit | MOVE_ONLY | 4           | `tests/unit/jobs_workers/create_owid_pages/test_owid_template_converter.py`                       |
| `tests/main_app/jobs_workers/crop_main_files/test_crop_file.py`                                       | unit | MOVE_ONLY | 12          | `tests/unit/jobs_workers/crop_main_files/test_crop_file.py`                                       |
| `tests/main_app/jobs_workers/crop_main_files/test_crop_main_files_worker.py`                          | unit | MOVE_ONLY | 23          | `tests/unit/jobs_workers/crop_main_files/test_crop_main_files_worker.py`                          |
| `tests/main_app/jobs_workers/crop_main_files/test_download.py`                                        | unit | MOVE_ONLY | 8           | `tests/unit/jobs_workers/crop_main_files/test_download.py`                                        |
| `tests/main_app/jobs_workers/crop_main_files/test_process_new.py`                                     | unit | MOVE_ONLY | 13          | `tests/unit/jobs_workers/crop_main_files/test_process_new.py`                                     |
| `tests/main_app/jobs_workers/crop_main_files/test_upload.py`                                          | unit | MOVE_ONLY | 3           | `tests/unit/jobs_workers/crop_main_files/test_upload.py`                                          |
| `tests/main_app/jobs_workers/test_base_worker.py`                                                     | —    | DELETE    | 0           | —                                                                                                 |
| `tests/main_app/jobs_workers/test_collect_main_files_worker.py`                                       | unit | MOVE_ONLY | 9           | `tests/unit/jobs_workers/test_collect_main_files_worker.py`                                       |
| `tests/main_app/jobs_workers/test_download_main_files_worker.py`                                      | unit | MOVE_ONLY | 9           | `tests/unit/jobs_workers/test_download_main_files_worker.py`                                      |
| `tests/main_app/jobs_workers/test_fix_nested_main_files_worker.py`                                    | unit | MOVE_ONLY | 10          | `tests/unit/jobs_workers/test_fix_nested_main_files_worker.py`                                    |
| `tests/main_app/jobs_workers/test_jobs_worker.py`                                                     | unit | MOVE_ONLY | 15          | `tests/unit/jobs_workers/test_jobs_worker.py`                                                     |
| `tests/main_app/jobs_workers/test_worker_cancellation.py`                                             | —    | DELETE    | 0           | —                                                                                                 |
| `tests/main_app/jobs_workers/utils/test_add_svglanguages_template_utils.py`                           | unit | MOVE_ONLY | 8           | `tests/unit/jobs_workers/utils/test_add_svglanguages_template_utils.py`                           |
| `tests/main_app/jobs_workers/utils/test_crop_main_files_utils.py`                                     | unit | MOVE_ONLY | 11          | `tests/unit/jobs_workers/utils/test_crop_main_files_utils.py`                                     |
| `tests/main_app/jobs_workers/utils/test_jobs_workers_utils.py`                                        | unit | MOVE_ONLY | 10          | `tests/unit/jobs_workers/utils/test_jobs_workers_utils.py`                                        |
| `tests/main_app/public_jobs_workers/copy_svg_langs/test_copy_svg_langs_processor.py`                  | unit | MOVE_ONLY | 5           | `tests/unit/public_jobs_workers/copy_svg_langs/test_copy_svg_langs_processor.py`                  |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_extracts_task.py`                | unit | MOVE_ONLY | 1           | `tests/unit/public_jobs_workers/copy_svg_langs_legacy/steps/test_extracts_task.py`                |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_fix_nested_tasks.py`             | unit | MOVE_ONLY | 2           | `tests/unit/public_jobs_workers/copy_svg_langs_legacy/steps/test_fix_nested_tasks.py`             |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_inject_tasks.py`                 | unit | MOVE_ONLY | 2           | `tests/unit/public_jobs_workers/copy_svg_langs_legacy/steps/test_inject_tasks.py`                 |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_start_bot.py`                    | unit | MOVE_ONLY | 2           | `tests/unit/public_jobs_workers/copy_svg_langs_legacy/steps/test_start_bot.py`                    |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_bot.py`                   | unit | MOVE_ONLY | 2           | `tests/unit/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_bot.py`                   |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_tasks.py`                 | unit | MOVE_ONLY | 4           | `tests/unit/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_tasks.py`                 |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_up.py`                           | unit | MOVE_ONLY | 3           | `tests/unit/public_jobs_workers/copy_svg_langs_legacy/steps/test_up.py`                           |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/test_legacy_threads.py`                     | unit | MOVE_ONLY | 1           | `tests/unit/public_jobs_workers/copy_svg_langs_legacy/test_legacy_threads.py`                     |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/test_legacy_worker.py`                      | —    | DELETE    | 0           | —                                                                                                 |
| `tests/main_app/services/test_admin_service.py`                                                       | unit | MOVE_ONLY | 7           | `tests/unit/services/test_admin_service.py`                                                       |
| `tests/main_app/services/test_jobs_service.py`                                                        | unit | MOVE_ONLY | 22          | `tests/unit/services/test_jobs_service.py`                                                        |
| `tests/main_app/services/test_owid_charts_service.py`                                                 | unit | MOVE_ONLY | 17          | `tests/unit/services/test_owid_charts_service.py`                                                 |
| `tests/main_app/services/test_template_service.py`                                                    | unit | MOVE_ONLY | 22          | `tests/unit/services/test_template_service.py`                                                    |
| `tests/main_app/users/test_current_unit.py`                                                           | unit | MOVE_ONLY | 4           | `tests/unit/users/test_current_unit.py`                                                           |
| `tests/main_app/users/test_store.py`                                                                  | unit | MOVE_ONLY | 19          | `tests/unit/users/test_store.py`                                                                  |
| `tests/main_app/users/test_users_store.py`                                                            | unit | MOVE_ONLY | 4           | `tests/unit/users/test_users_store.py`                                                            |
| `tests/main_app/utils/api_services_utils/test_download_file_utils.py`                                 | unit | MOVE_ONLY | 10          | `tests/unit/utils/api_services_utils/test_download_file_utils.py`                                 |
| `tests/main_app/utils/categories_utils/test_capitalize_category.py`                                   | unit | MOVE_ONLY | 4           | `tests/unit/utils/categories_utils/test_capitalize_category.py`                                   |
| `tests/main_app/utils/categories_utils/test_categories_utils.py`                                      | unit | MOVE_ONLY | 4           | `tests/unit/utils/categories_utils/test_categories_utils.py`                                      |
| `tests/main_app/utils/categories_utils/test_extract_categories.py`                                    | unit | MOVE_ONLY | 7           | `tests/unit/utils/categories_utils/test_extract_categories.py`                                    |
| `tests/main_app/utils/categories_utils/test_find_missing_categories.py`                               | unit | MOVE_ONLY | 9           | `tests/unit/utils/categories_utils/test_find_missing_categories.py`                               |
| `tests/main_app/utils/categories_utils/test_merge_categories.py`                                      | unit | MOVE_ONLY | 8           | `tests/unit/utils/categories_utils/test_merge_categories.py`                                      |
| `tests/main_app/utils/test_jinja_filters.py`                                                          | unit | MOVE_ONLY | 6           | `tests/unit/utils/test_jinja_filters.py`                                                          |
| `tests/main_app/utils/test_verify.py`                                                                 | —    | DELETE    | 0           | —                                                                                                 |
| `tests/main_app/utils/wikitext/temps_bot/test_get_files_list.py`                                      | unit | MOVE_ONLY | 4           | `tests/unit/utils/wikitext/temps_bot/test_get_files_list.py`                                      |
| `tests/main_app/utils/wikitext/temps_bot/test_get_titles.py`                                          | unit | MOVE_ONLY | 5           | `tests/unit/utils/wikitext/temps_bot/test_get_titles.py`                                          |
| `tests/main_app/utils/wikitext/temps_bot/test_temps_bot.py`                                           | unit | MOVE_ONLY | 10          | `tests/unit/utils/wikitext/temps_bot/test_temps_bot.py`                                           |
| `tests/main_app/utils/wikitext/test_appendImageExtractedTemplate.py`                                  | unit | MOVE_ONLY | 3           | `tests/unit/utils/wikitext/test_appendImageExtractedTemplate.py`                                  |
| `tests/main_app/utils/wikitext/test_before_methods.py`                                                | unit | MOVE_ONLY | 3           | `tests/unit/utils/wikitext/test_before_methods.py`                                                |
| `tests/main_app/utils/wikitext/test_files_text.py`                                                    | unit | MOVE_ONLY | 11          | `tests/unit/utils/wikitext/test_files_text.py`                                                    |
| `tests/main_app/utils/wikitext/test_other_versions.py`                                                | unit | MOVE_ONLY | 4           | `tests/unit/utils/wikitext/test_other_versions.py`                                                |
| `tests/main_app/utils/wikitext/test_temp_source.py`                                                   | unit | MOVE_ONLY | 11          | `tests/unit/utils/wikitext/test_temp_source.py`                                                   |
| `tests/main_app/utils/wikitext/test_template_page.py`                                                 | unit | MOVE_ONLY | 5           | `tests/unit/utils/wikitext/test_template_page.py`                                                 |
| `tests/main_app/utils/wikitext/test_text_utils.py`                                                    | unit | MOVE_ONLY | 3           | `tests/unit/utils/wikitext/test_text_utils.py`                                                    |
| `tests/main_app/utils/wikitext/test_update_original_file_text.py`                                     | unit | MOVE_ONLY | 18          | `tests/unit/utils/wikitext/test_update_original_file_text.py`                                     |
| `tests/main_app/utils/wikitext/test_update_template_page_file_reference.py`                           | unit | MOVE_ONLY | 5           | `tests/unit/utils/wikitext/test_update_template_page_file_reference.py`                           |
| `tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py`            | unit | MOVE_ONLY | 11          | `tests/unit/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py`            |
| `tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py`           | unit | MOVE_ONLY | 9           | `tests/unit/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py`           |
| `tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py` | unit | MOVE_ONLY | 37          | `tests/unit/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py` |
| `tests/main_app/utils/wikitext/titles_utils/test_find_main_title.py`                                  | unit | MOVE_ONLY | 9           | `tests/unit/utils/wikitext/titles_utils/test_find_main_title.py`                                  |
| `tests/main_app/utils/wikitext/titles_utils/test_last_world_file_with_full_date.py`                   | unit | MOVE_ONLY | 11          | `tests/unit/utils/wikitext/titles_utils/test_last_world_file_with_full_date.py`                   |
| `tests/main_app/utils/wikitext/titles_utils/test_main_file.py`                                        | unit | MOVE_ONLY | 11          | `tests/unit/utils/wikitext/titles_utils/test_main_file.py`                                        |
| `tests/main_app/utils/wikitext/titles_utils/test_match_main_title.py`                                 | unit | MOVE_ONLY | 9           | `tests/unit/utils/wikitext/titles_utils/test_match_main_title.py`                                 |
| `tests/main_app/test_init.py`                                                                         | unit | MOVE_ONLY | 9           | `tests/unit/test_init.py`                                                                         |
| `tests/main_app/test_app_factory.py`                                                                  | unit | MOVE_ONLY | 10          | `tests/unit/test_app_factory.py`                                                                  |
| `tests/main_app/test_config.py`                                                                       | unit | MOVE_ONLY | 15          | `tests/unit/test_config.py`                                                                       |
| `tests/main_app/test_data.py`                                                                         | unit | MOVE_ONLY | 1           | `tests/unit/test_data.py`                                                                         |

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
git mv tests/main_app/admins/test_admins_required.py tests/unit/admins/test_admins_required.py

# api_services/clients
git mv tests/main_app/api_services/clients/test_commons_client.py tests/unit/api_services/clients/test_commons_client.py
git mv tests/main_app/api_services/clients/test_wiki_client.py tests/unit/api_services/clients/test_wiki_client.py

# api_services/mwclient_page
git mv tests/main_app/api_services/mwclient_page/test_mwclient_page.py tests/unit/api_services/mwclient_page/test_mwclient_page.py
git mv tests/main_app/api_services/mwclient_page/test_mwclient_page2.py tests/unit/api_services/mwclient_page/test_mwclient_page2.py

# api_services (root)
git mv tests/main_app/api_services/test_category.py tests/unit/api_services/test_category.py
git mv tests/main_app/api_services/test_pages_api.py tests/unit/api_services/test_pages_api.py
git mv tests/main_app/api_services/test_text_api.py tests/unit/api_services/test_text_api.py
git mv tests/main_app/api_services/test_text_bot.py tests/unit/api_services/test_text_bot.py
git mv tests/main_app/api_services/test_upload_bot.py tests/unit/api_services/test_upload_bot.py
git mv tests/main_app/api_services/test_upload_bot_new.py tests/unit/api_services/test_upload_bot_new.py

# app_routes/admin/admin_routes
git mv tests/main_app/app_routes/admin/admin_routes/test_coordinators_exception_handling.py tests/unit/app_routes/admin/admin_routes/test_coordinators_exception_handling.py

# app_routes/admin
git mv tests/main_app/app_routes/admin/test_sidebar.py tests/unit/app_routes/admin/test_sidebar.py

# app_routes/auth
git mv tests/main_app/app_routes/auth/test_auth_cookie.py tests/unit/app_routes/auth/test_auth_cookie.py
git mv tests/main_app/app_routes/auth/test_auth_oauth_helpers.py tests/unit/app_routes/auth/test_auth_oauth_helpers.py
git mv tests/main_app/app_routes/auth/test_cookie.py tests/unit/app_routes/auth/test_cookie.py
git mv tests/main_app/app_routes/auth/test_oauth.py tests/unit/app_routes/auth/test_oauth.py
git mv tests/main_app/app_routes/auth/test_rate_limit.py tests/unit/app_routes/auth/test_rate_limit.py

# app_routes/fix_nested
git mv tests/main_app/app_routes/fix_nested/test_explorer_routes_undo.py tests/unit/app_routes/fix_nested/test_explorer_routes_undo.py
git mv tests/main_app/app_routes/fix_nested/test_fix_nested_routes_unit.py tests/unit/app_routes/fix_nested/test_fix_nested_routes_unit.py
git mv tests/main_app/app_routes/fix_nested/test_fix_nested_worker.py tests/unit/app_routes/fix_nested/test_fix_nested_worker.py

# app_routes/utils
git mv tests/main_app/app_routes/utils/test_args_utils.py tests/unit/app_routes/utils/test_args_utils.py
git mv tests/main_app/app_routes/utils/test_compare.py tests/unit/app_routes/utils/test_compare.py
git mv tests/main_app/app_routes/utils/test_explorer_utils.py tests/unit/app_routes/utils/test_explorer_utils.py
git mv tests/main_app/app_routes/utils/test_fix_nested_utils.py tests/unit/app_routes/utils/test_fix_nested_utils.py
git mv tests/main_app/app_routes/utils/test_routes_utils_unit.py tests/unit/app_routes/utils/test_routes_utils_unit.py
git mv tests/main_app/app_routes/utils/test_thumbnail_utils.py tests/unit/app_routes/utils/test_thumbnail_utils.py

# core
git mv tests/main_app/core/test_crypto.py tests/unit/core/test_crypto.py

# db
git mv tests/main_app/db/test_db_class.py tests/unit/db/test_db_class.py
git mv tests/main_app/db/test_db_CoordinatorsDB.py tests/unit/db/test_db_CoordinatorsDB.py
git mv tests/main_app/db/test_db_Jobs.py tests/unit/db/test_db_Jobs.py
git mv tests/main_app/db/test_db_OwidCharts.py tests/unit/db/test_db_OwidCharts.py
git mv tests/main_app/db/test_db_Settings.py tests/unit/db/test_db_Settings.py
git mv tests/main_app/db/test_db_Templates.py tests/unit/db/test_db_Templates.py
git mv tests/main_app/db/test_exceptions.py tests/unit/db/test_exceptions.py
git mv tests/main_app/db/test_fix_nested_task_store.py tests/unit/db/test_fix_nested_task_store.py
git mv tests/main_app/db/test_svg_db.py tests/unit/db/test_svg_db.py

# jobs_workers/add_svglanguages_template
git mv tests/main_app/jobs_workers/add_svglanguages_template/test_add_svglanguages_template_worker.py tests/unit/jobs_workers/add_svglanguages_template/test_add_svglanguages_template_worker.py

# jobs_workers/create_owid_pages
git mv tests/main_app/jobs_workers/create_owid_pages/test_create_owid_pages_worker.py tests/unit/jobs_workers/create_owid_pages/test_create_owid_pages_worker.py
git mv tests/main_app/jobs_workers/create_owid_pages/test_owid_template_converter.py tests/unit/jobs_workers/create_owid_pages/test_owid_template_converter.py

# jobs_workers/crop_main_files
git mv tests/main_app/jobs_workers/crop_main_files/test_crop_file.py tests/unit/jobs_workers/crop_main_files/test_crop_file.py
git mv tests/main_app/jobs_workers/crop_main_files/test_crop_main_files_worker.py tests/unit/jobs_workers/crop_main_files/test_crop_main_files_worker.py
git mv tests/main_app/jobs_workers/crop_main_files/test_download.py tests/unit/jobs_workers/crop_main_files/test_download.py
git mv tests/main_app/jobs_workers/crop_main_files/test_process_new.py tests/unit/jobs_workers/crop_main_files/test_process_new.py
git mv tests/main_app/jobs_workers/crop_main_files/test_upload.py tests/unit/jobs_workers/crop_main_files/test_upload.py

# jobs_workers (root)
git mv tests/main_app/jobs_workers/test_collect_main_files_worker.py tests/unit/jobs_workers/test_collect_main_files_worker.py
git mv tests/main_app/jobs_workers/test_download_main_files_worker.py tests/unit/jobs_workers/test_download_main_files_worker.py
git mv tests/main_app/jobs_workers/test_fix_nested_main_files_worker.py tests/unit/jobs_workers/test_fix_nested_main_files_worker.py
git mv tests/main_app/jobs_workers/test_jobs_worker.py tests/unit/jobs_workers/test_jobs_worker.py

# jobs_workers/utils
git mv tests/main_app/jobs_workers/utils/test_add_svglanguages_template_utils.py tests/unit/jobs_workers/utils/test_add_svglanguages_template_utils.py
git mv tests/main_app/jobs_workers/utils/test_crop_main_files_utils.py tests/unit/jobs_workers/utils/test_crop_main_files_utils.py
git mv tests/main_app/jobs_workers/utils/test_jobs_workers_utils.py tests/unit/jobs_workers/utils/test_jobs_workers_utils.py

# public_jobs_workers/copy_svg_langs
git mv tests/main_app/public_jobs_workers/copy_svg_langs/test_copy_svg_langs_processor.py tests/unit/public_jobs_workers/copy_svg_langs/test_copy_svg_langs_processor.py

# public_jobs_workers/copy_svg_langs_legacy/steps
git mv tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_extracts_task.py tests/unit/public_jobs_workers/copy_svg_langs_legacy/steps/test_extracts_task.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_fix_nested_tasks.py tests/unit/public_jobs_workers/copy_svg_langs_legacy/steps/test_fix_nested_tasks.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_inject_tasks.py tests/unit/public_jobs_workers/copy_svg_langs_legacy/steps/test_inject_tasks.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_start_bot.py tests/unit/public_jobs_workers/copy_svg_langs_legacy/steps/test_start_bot.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_bot.py tests/unit/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_bot.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_tasks.py tests/unit/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_tasks.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_up.py tests/unit/public_jobs_workers/copy_svg_langs_legacy/steps/test_up.py

# public_jobs_workers/copy_svg_langs_legacy (root)
git mv tests/main_app/public_jobs_workers/copy_svg_langs_legacy/test_legacy_threads.py tests/unit/public_jobs_workers/copy_svg_langs_legacy/test_legacy_threads.py

# services
git mv tests/main_app/services/test_admin_service.py tests/unit/services/test_admin_service.py
git mv tests/main_app/services/test_jobs_service.py tests/unit/services/test_jobs_service.py
git mv tests/main_app/services/test_owid_charts_service.py tests/unit/services/test_owid_charts_service.py
git mv tests/main_app/services/test_template_service.py tests/unit/services/test_template_service.py

# users
git mv tests/main_app/users/test_current_unit.py tests/unit/users/test_current_unit.py
git mv tests/main_app/users/test_store.py tests/unit/users/test_store.py
git mv tests/main_app/users/test_users_store.py tests/unit/users/test_users_store.py

# utils/api_services_utils
git mv tests/main_app/utils/api_services_utils/test_download_file_utils.py tests/unit/utils/api_services_utils/test_download_file_utils.py

# utils/categories_utils
git mv tests/main_app/utils/categories_utils/test_capitalize_category.py tests/unit/utils/categories_utils/test_capitalize_category.py
git mv tests/main_app/utils/categories_utils/test_categories_utils.py tests/unit/utils/categories_utils/test_categories_utils.py
git mv tests/main_app/utils/categories_utils/test_extract_categories.py tests/unit/utils/categories_utils/test_extract_categories.py
git mv tests/main_app/utils/categories_utils/test_find_missing_categories.py tests/unit/utils/categories_utils/test_find_missing_categories.py
git mv tests/main_app/utils/categories_utils/test_merge_categories.py tests/unit/utils/categories_utils/test_merge_categories.py

# utils (root)
git mv tests/main_app/utils/test_jinja_filters.py tests/unit/utils/test_jinja_filters.py

# utils/wikitext/temps_bot
git mv tests/main_app/utils/wikitext/temps_bot/test_get_files_list.py tests/unit/utils/wikitext/temps_bot/test_get_files_list.py
git mv tests/main_app/utils/wikitext/temps_bot/test_get_titles.py tests/unit/utils/wikitext/temps_bot/test_get_titles.py
git mv tests/main_app/utils/wikitext/temps_bot/test_temps_bot.py tests/unit/utils/wikitext/temps_bot/test_temps_bot.py

# utils/wikitext (root)
git mv tests/main_app/utils/wikitext/test_appendImageExtractedTemplate.py tests/unit/utils/wikitext/test_appendImageExtractedTemplate.py
git mv tests/main_app/utils/wikitext/test_before_methods.py tests/unit/utils/wikitext/test_before_methods.py
git mv tests/main_app/utils/wikitext/test_files_text.py tests/unit/utils/wikitext/test_files_text.py
git mv tests/main_app/utils/wikitext/test_other_versions.py tests/unit/utils/wikitext/test_other_versions.py
git mv tests/main_app/utils/wikitext/test_temp_source.py tests/unit/utils/wikitext/test_temp_source.py
git mv tests/main_app/utils/wikitext/test_template_page.py tests/unit/utils/wikitext/test_template_page.py
git mv tests/main_app/utils/wikitext/test_text_utils.py tests/unit/utils/wikitext/test_text_utils.py
git mv tests/main_app/utils/wikitext/test_update_original_file_text.py tests/unit/utils/wikitext/test_update_original_file_text.py
git mv tests/main_app/utils/wikitext/test_update_template_page_file_reference.py tests/unit/utils/wikitext/test_update_template_page_file_reference.py

# utils/wikitext/titles_utils/last_world_file_utils
git mv tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py tests/unit/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py
git mv tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py tests/unit/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py
git mv tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py tests/unit/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py

# utils/wikitext/titles_utils
git mv tests/main_app/utils/wikitext/titles_utils/test_find_main_title.py tests/unit/utils/wikitext/titles_utils/test_find_main_title.py
git mv tests/main_app/utils/wikitext/titles_utils/test_last_world_file_with_full_date.py tests/unit/utils/wikitext/titles_utils/test_last_world_file_with_full_date.py
git mv tests/main_app/utils/wikitext/titles_utils/test_main_file.py tests/unit/utils/wikitext/titles_utils/test_main_file.py
git mv tests/main_app/utils/wikitext/titles_utils/test_match_main_title.py tests/unit/utils/wikitext/titles_utils/test_match_main_title.py

# root tests/main_app/
git mv tests/main_app/test_init.py tests/unit/test_init.py
git mv tests/main_app/test_app_factory.py tests/unit/test_app_factory.py
git mv tests/main_app/test_config.py tests/unit/test_config.py
git mv tests/main_app/test_data.py tests/unit/test_data.py

# ── Delete empty TODO stubs ──────────────────────────────────────────────────
git rm tests/main_app/jobs_workers/test_base_worker.py
git rm tests/main_app/jobs_workers/test_worker_cancellation.py
git rm tests/main_app/public_jobs_workers/copy_svg_langs_legacy/test_legacy_worker.py
git rm tests/main_app/utils/test_verify.py
```

---
