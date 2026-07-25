# monkeypatch.setattr() Usage Report

Generated for `tests/` directory.

## Summary

| Metric                                        | Value |
| --------------------------------------------- | ----- |
| Total files containing `monkeypatch.setattr(` | 77    |
| Total `monkeypatch.setattr(` calls            | 622   |

## Full File List

| #   | File                                                                                                      | Count | Status                 |
| --- | --------------------------------------------------------------------------------------------------------- | ----- | ---------------------- |
| 1   | `tests/unit/admin/routes/test_coordinators.py`                                                            | 10    |                        |
| 2   | `tests/unit/admin/routes/test_owid_charts.py`                                                             | 6     |                        |
| 3   | `tests/unit/admin/routes/test_users_routes.py`                                                            | 10    | ✅ refactored (was 30) |
| 4   | `tests/unit/db/services/test_settings_service.py`                                                         | 5     | ✅ refactored (was 29) |
| 5   | `tests/unit/admin/routes/test_slug_redirects.py`                                                          | 25    | 🔴 refactor candidate  |
| 6   | `tests/unit/db/services/test_jobs_service.py`                                                             | 23    | 🔴 refactor candidate  |
| 7   | `tests/unit/admin/routes/test_settings.py`                                                                | 23    | 🔴 refactor candidate  |
| 8   | `tests/integration/admin/routes/test_admin_jobs_routes.py`                                                | 23    | 🔴 refactor candidate  |
| 9   | `tests/unit/jobs_workers/public_jobs_workers/copy_svg_langs/test_copy_svg_langs_worker.py`                | 22    | 🟡                     |
| 10  | `tests/unit/public/test_public_jobs.py`                                                                   | 20    | ✅ refactored (was 85) |
| 11  | `tests/unit/public/test_jobs_utils_bp.py`                                                                 | 19    | 🟠 borderline          |
| 12  | `tests/integration/public/auth/test_auth_routes.py`                                                       | 19    | 🟠 borderline          |
| 13  | `tests/unit/jobs_workers/admin_jobs_workers/crop_main_files/test_crop_main_files_worker.py`               | 18    | 🟠 borderline          |
| 14  | `tests/unit/db/services/test_user_token_service.py`                                                       | 16    | 🟠 borderline          |
| 15  | `tests/integration/public/main_routes/test_extract_routes_integration.py`                                 | 16    | 🟠 borderline          |
| 16  | `tests/integration/public/main_routes/test_explorer_routes_integration.py`                                | 15    | 🟠 borderline          |
| 17  | `tests/unit/jobs_workers/admin_jobs_workers/collect_templates_data/test_template_data_usage.py`           | 12    |                        |
| 18  | `tests/unit/jobs_workers/admin_jobs_workers/collect_templates_data/conftest.py`                           | 11    |                        |
| 19  | `tests/unit/db/services/test_owid_charts_service.py`                                                      | 11    |                        |
| 20  | `tests/unit/shared/auth/test_mwoauth_handshake.py`                                                        | 10    |                        |
| 21  | `tests/unit/public/test_profile.py`                                                                       | 10    |                        |
| 22  | `tests/unit/admin/routes/test_templates.py`                                                               | 10    |                        |
| 23  | `tests/unit/public/auth/test_auth_utils.py`                                                               | 9     |                        |
| 24  | `tests/unit/jobs_workers/admin_jobs_workers/fix_nested_main_files/conftest.py`                            | 8     |                        |
| 25  | `tests/unit/jobs_workers/admin_jobs_workers/create_owid_pages/conftest.py`                                | 8     |                        |
| 26  | `tests/unit/jobs_workers/public_jobs_workers/fix_nested_jobs/conftest.py`                                 | 7     |                        |
| 27  | `tests/unit/jobs_workers/public_jobs_workers/copy_svg_langs/steps/test_extract_translations.py`           | 7     |                        |
| 28  | `tests/unit/jobs_workers/admin_jobs_workers/update_owid_charts/test_update_owid_charts_worker.py`         | 7     |                        |
| 29  | `tests/unit/shared/auth/test_auth_users_service.py`                                                       | 6     |                        |
| 30  | `tests/unit/public/auth/test_routes.py`                                                                   | 6     |                        |
| 31  | `tests/unit/jobs_workers/admin_jobs_workers/download_main_files/test_download_main_files_runner.py`       | 6     |                        |
| 32  | `tests/unit/conftest.py`                                                                                  | 6     |                        |
| 33  | `tests/unit/admin/test_admins_required.py`                                                                | 6     |                        |
| 34  | `tests/unit/jobs_workers/admin_jobs_workers/test_jobs_worker.py`                                          | 5     |                        |
| 35  | `tests/unit/jobs_workers/admin_jobs_workers/rename_owid_pages/test_rename_owid_pages_worker.py`           | 5     |                        |
| 36  | `tests/unit/jobs_workers/admin_jobs_workers/collect_templates_data/test_collect_worker_cancellation.py`   | 5     |                        |
| 37  | `tests/unit/jobs_workers/admin_jobs_workers/add_svglanguages_template/conftest.py`                        | 5     |                        |
| 38  | `tests/unit/admin/routes/test_coordinators_exception_handling.py`                                         | 5     |                        |
| 39  | `tests/unit/jobs_workers/test_jobs_worker_logic.py`                                                       | 4     |                        |
| 40  | `tests/unit/jobs_workers/admin_jobs_workers/test_jobs_files_service.py`                                   | 4     |                        |
| 41  | `tests/integration/conftest.py`                                                                           | 4     |                        |
| 42  | `tests/integration/admin/routes/test_templates_integration.py`                                            | 4     |                        |
| 43  | `tests/integration/admin/routes/test_templates_admin_routes_integration.py`                               | 4     |                        |
| 44  | `tests/integration/admin/routes/test_owid_charts_integration.py`                                          | 4     |                        |
| 45  | `tests/unit/public/test_api_routes.py`                                                                    | 3     |                        |
| 46  | `tests/unit/jobs_workers/admin_jobs_workers/add_lang_categories_to_owid_pages/conftest.py`                | 3     |                        |
| 47  | `tests/unit/api_services/files_service/test_download_file_utils.py`                                       | 3     |                        |
| 48  | `tests/unit/api_services/clients/test_owid_client.py`                                                     | 3     |                        |
| 49  | `tests/integration/admin/test_admin_routes.py`                                                            | 3     |                        |
| 50  | `tests/unit/shared/fix_nested/test_fix_nested_worker.py`                                                  | 2     |                        |
| 51  | `tests/unit/jobs_workers/test_base_worker_object.py`                                                      | 2     |                        |
| 52  | `tests/unit/jobs_workers/admin_jobs_workers/fix_nested_main_files/test_fix_worker_cancellation.py`        | 2     |                        |
| 53  | `tests/unit/jobs_workers/admin_jobs_workers/collect_templates_data/test_collect_templates_data_runner.py` | 2     |                        |
| 54  | `tests/unit/api_services/test_query_api.py`                                                               | 2     |                        |
| 55  | `tests/unit/api_services/files_service/test_files_helpers.py`                                             | 2     |                        |
| 56  | `tests/unit/api_services/clients/test_wiki_client.py`                                                     | 2     |                        |
| 57  | `tests/test_logger_config.py`                                                                             | 2     |                        |
| 58  | `tests/integration/public/test_jobs_utils_bp_routes_integration.py`                                       | 2     |                        |
| 59  | `tests/unit/public/utils/test_explorer_utils.py`                                                          | 1     |                        |
| 60  | `tests/unit/jobs_workers/public_jobs_workers/fix_nested_jobs/test_fix_nested_jobs_worker.py`              | 1     |                        |
| 61  | `tests/unit/jobs_workers/public_jobs_workers/copy_svg_langs/test_copy_svg_langs_runner.py`                | 1     |                        |
| 62  | `tests/unit/jobs_workers/public_jobs_workers/copy_svg_langs/steps/test_inject_one_file.py`                | 1     |                        |
| 63  | `tests/unit/jobs_workers/public_jobs_workers/copy_svg_langs/steps/test_extract_titles.py`                 | 1     |                        |
| 64  | `tests/unit/jobs_workers/public_jobs_workers/copy_svg_langs/steps/test_extract_text.py`                   | 1     |                        |
| 65  | `tests/unit/jobs_workers/admin_jobs_workers/rename_owid_pages/test_rename_owid_pages_runner.py`           | 1     |                        |
| 66  | `tests/unit/jobs_workers/admin_jobs_workers/download_main_files/test_download_helper.py`                  | 1     |                        |
| 67  | `tests/unit/jobs_workers/admin_jobs_workers/crop_main_files/test_crop_main_files_runner.py`               | 1     |                        |
| 68  | `tests/unit/db/services/utils/test_retry_on_disconnect.py`                                                | 1     |                        |
| 69  | `tests/unit/db/services/utils/test_detachedinstanceerror.py`                                              | 1     |                        |
| 70  | `tests/unit/db/services/test_template_service.py`                                                         | 1     |                        |
| 71  | `tests/unit/db/services/test_owid_slug_redirects_service.py`                                              | 1     |                        |
| 72  | `tests/unit/api_services/mwclient_page/test_mwclient_wraper.py`                                           | 1     |                        |
| 73  | `tests/unit/api_services/mwclient_page/test_mwclient_page.py`                                             | 1     |                        |
| 74  | `tests/unit/api_services/files_service/test_upload_bot.py`                                                | 1     |                        |
| 75  | `tests/integration/public/main_routes/test_owid_charts_routes_integration.py`                             | 1     |                        |
| 76  | `tests/integration/public/auth/test_oauth_helpers_integration.py`                                         | 1     |                        |
| 77  | `tests/integration/api_services/files_service/test_upload_bot_integration.py`                             | 1     |                        |

## Refactoring Progress

### ✅ Refactored files

| File                       | Before  | After  | Reduction |
| -------------------------- | ------- | ------ | --------- |
| `test_public_jobs.py`      | 85      | 20     | 76%       |
| `test_users_routes.py`     | 30      | 10     | 67%       |
| `test_settings_service.py` | 29      | 5      | 83%       |
| **Total**                  | **144** | **35** | **76%**   |

### 🔴 Remaining high-priority candidates (≥20 calls)

| File                            | Count |
| ------------------------------- | ----- |
| `test_slug_redirects.py`        | 25    |
| `test_jobs_service.py`          | 23    |
| `test_settings.py`              | 23    |
| `test_admin_jobs_routes.py`     | 23    |
| `test_copy_svg_langs_worker.py` | 22    |

## Recommended Refactoring Patterns

| Pattern                                           | When to apply                                                      |
| ------------------------------------------------- | ------------------------------------------------------------------ |
| **Many individual mocks → `@dataclass` bundle**   | 5+ separate `monkeypatch.setattr` for related service dependencies |
| **Repeated `@patch` decorators → fixture**        | Same `@patch("path")` on ≥2 test functions                         |
| **Repeated in-body mock setup → factory fixture** | 3+ identical mock construction lines copy-pasted across tests      |
