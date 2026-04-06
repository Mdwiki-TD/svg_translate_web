# Test Classification Report - main_app

## Summary Statistics
- Total files analyzed: 102
- Files MOVE_ONLY → unit: 96
- Files MOVE_ONLY → integration: 1
- Files MOVE_ONLY → functional: 0
- Files to SPLIT: 3
- Files to DELETE: 2

## Detailed Classification Table
| File | Type | Action | Tests Count | Destination |
| --- | --- | --- | --- | --- |
| `tests/main_app/admins/test_admins_required.py` | unit | MOVE_ONLY | 6 | tests/unit/main_app/app_routes/admin/test_admins_required.py |
| `tests/main_app/api_services/clients/test_commons_client.py` | unit | MOVE_ONLY | 10 | tests/unit/main_app/api_services/clients/test_commons_client.py |
| `tests/main_app/api_services/clients/test_wiki_client.py` | unit | MOVE_ONLY | 1 | tests/unit/main_app/api_services/clients/test_wiki_client.py |
| `tests/main_app/api_services/mwclient_page/test_mwclient_page.py` | unit | MOVE_ONLY | 21 | tests/unit/main_app/api_services/test_mwclient_page.py |
| `tests/main_app/api_services/mwclient_page/test_mwclient_page2.py` | unit | MOVE_ONLY | 7 | tests/unit/main_app/api_services/test_mwclient_page2.py |
| `tests/main_app/api_services/test_category.py` | unit | MOVE_ONLY | 11 | tests/unit/main_app/api_services/test_category.py |
| `tests/main_app/api_services/test_pages_api.py` | unit | MOVE_ONLY | 27 | tests/unit/main_app/api_services/test_pages_api.py |
| `tests/main_app/api_services/test_text_api.py` | unit | MOVE_ONLY | 14 | tests/unit/main_app/api_services/test_text_api.py |
| `tests/main_app/api_services/test_text_bot.py` | unit | MOVE_ONLY | 3 | tests/unit/main_app/api_services/test_text_bot.py |
| `tests/main_app/api_services/test_upload_bot.py` | unit | MOVE_ONLY | 5 | tests/unit/main_app/api_services/test_upload_bot.py |
| `tests/main_app/api_services/test_upload_bot_new.py` | unit | MOVE_ONLY | 39 | tests/unit/main_app/api_services/test_upload_bot_new.py |
| `tests/main_app/app_routes/admin/admin_routes/test_coordinators_exception_handling.py` | unit | MOVE_ONLY | 1 | tests/unit/main_app/app_routes/app_routes/admin_routes/test_coordinators_exception_handling.py |
| `tests/main_app/app_routes/admin/test_sidebar.py` | unit | MOVE_ONLY | 13 | tests/unit/main_app/app_routes/admin/test_sidebar.py |
| `tests/main_app/app_routes/auth/test_auth_cookie.py` | unit | MOVE_ONLY | 4 | tests/unit/main_app/app_routes/auth/test_auth_cookie.py |
| `tests/main_app/app_routes/auth/test_auth_oauth_helpers.py` | mixed | SPLIT | 3 | unit(2) + integration(1) |
| `tests/main_app/app_routes/auth/test_cookie.py` | unit | MOVE_ONLY | 7 | tests/unit/main_app/app_routes/auth/test_cookie.py |
| `tests/main_app/app_routes/auth/test_oauth.py` | unit | MOVE_ONLY | 6 | tests/unit/main_app/app_routes/auth/test_oauth.py |
| `tests/main_app/app_routes/auth/test_rate_limit.py` | unit | MOVE_ONLY | 3 | tests/unit/main_app/app_routes/auth/test_rate_limit.py |
| `tests/main_app/app_routes/fix_nested/test_explorer_routes_undo.py` | unit | MOVE_ONLY | 2 | tests/unit/main_app/app_routes/fix_nested/test_explorer_routes_undo.py |
| `tests/main_app/app_routes/fix_nested/test_fix_nested_routes_unit.py` | unit | MOVE_ONLY | 3 | tests/unit/main_app/app_routes/fix_nested/test_fix_nested_routes_unit.py |
| `tests/main_app/app_routes/fix_nested/test_fix_nested_worker.py` | unit | MOVE_ONLY | 18 | tests/unit/main_app/app_routes/fix_nested/test_fix_nested_worker.py |
| `tests/main_app/app_routes/utils/test_args_utils.py` | unit | MOVE_ONLY | 14 | tests/unit/main_app/app_routes/utils/test_args_utils.py |
| `tests/main_app/app_routes/utils/test_compare.py` | unit | MOVE_ONLY | 3 | tests/unit/main_app/app_routes/utils/test_compare.py |
| `tests/main_app/app_routes/utils/test_explorer_utils.py` | unit | MOVE_ONLY | 5 | tests/unit/main_app/app_routes/utils/test_explorer_utils.py |
| `tests/main_app/app_routes/utils/test_fix_nested_utils.py` | unit | MOVE_ONLY | 10 | tests/unit/main_app/app_routes/utils/test_fix_nested_utils.py |
| `tests/main_app/app_routes/utils/test_routes_utils_unit.py` | unit | MOVE_ONLY | 4 | tests/unit/main_app/app_routes/utils/test_routes_utils.py |
| `tests/main_app/app_routes/utils/test_thumbnail_utils.py` | unit | MOVE_ONLY | 1 | tests/unit/main_app/app_routes/utils/test_thumbnail_utils.py |
| `tests/main_app/core/test_crypto.py` | unit | MOVE_ONLY | 1 | tests/unit/main_app/core/test_crypto.py |
| `tests/main_app/db/test_db_class.py` | unit | MOVE_ONLY | 8 | tests/unit/main_app/db/test_db_class.py |
| `tests/main_app/db/test_db_CoordinatorsDB.py` | unit | MOVE_ONLY | 23 | tests/unit/main_app/db/test_db_CoordinatorsDB.py |
| `tests/main_app/db/test_db_Jobs.py` | unit | MOVE_ONLY | 19 | tests/unit/main_app/db/test_db_Jobs.py |
| `tests/main_app/db/test_db_OwidCharts.py` | unit | MOVE_ONLY | 21 | tests/unit/main_app/db/test_db_OwidCharts.py |
| `tests/main_app/db/test_db_Settings.py` | unit | MOVE_ONLY | 29 | tests/unit/main_app/db/test_db_Settings.py |
| `tests/main_app/db/test_db_Templates.py` | unit | MOVE_ONLY | 18 | tests/unit/main_app/db/test_db_Templates.py |
| `tests/main_app/db/test_exceptions.py` | unit | MOVE_ONLY | 1 | tests/unit/main_app/db/test_exceptions.py |
| `tests/main_app/db/test_fix_nested_task_store.py` | unit | MOVE_ONLY | 13 | tests/unit/main_app/db/test_fix_nested_task_store.py |
| `tests/main_app/db/test_svg_db.py` | unit | MOVE_ONLY | 6 | tests/unit/main_app/db/test_svg_db.py |
| `tests/main_app/jobs_workers/add_svglanguages_template/test_add_svglanguages_template_worker.py` | unit | MOVE_ONLY | 28 | tests/unit/main_app/jobs_workers/add_svglanguages_template/test_add_svglanguages_template_worker.py |
| `tests/main_app/jobs_workers/create_owid_pages/test_create_owid_pages_worker.py` | unit | MOVE_ONLY | 33 | tests/unit/main_app/jobs_workers/create_owid_pages/test_create_owid_pages_worker.py |
| `tests/main_app/jobs_workers/create_owid_pages/test_owid_template_converter.py` | unit | MOVE_ONLY | 1 | tests/unit/main_app/jobs_workers/create_owid_pages/test_owid_template_converter.py |
| `tests/main_app/jobs_workers/crop_main_files/test_crop_file.py` | unit | MOVE_ONLY | 22 | tests/unit/main_app/jobs_workers/crop_main_files/test_crop_file.py |
| `tests/main_app/jobs_workers/crop_main_files/test_crop_main_files_worker.py` | unit | MOVE_ONLY | 20 | tests/unit/main_app/jobs_workers/crop_main_files/test_crop_main_files_worker.py |
| `tests/main_app/jobs_workers/crop_main_files/test_download.py` | unit | MOVE_ONLY | 7 | tests/unit/main_app/jobs_workers/crop_main_files/test_download.py |
| `tests/main_app/jobs_workers/crop_main_files/test_process_new.py` | unit | MOVE_ONLY | 40 | tests/unit/main_app/jobs_workers/crop_main_files/test_process_new.py |
| `tests/main_app/jobs_workers/crop_main_files/test_upload.py` | unit | MOVE_ONLY | 17 | tests/unit/main_app/jobs_workers/crop_main_files/test_upload.py |
| `tests/main_app/jobs_workers/test_base_worker.py` | unit | MOVE_ONLY | 15 | tests/unit/main_app/jobs_workers/test_base_worker.py |
| `tests/main_app/jobs_workers/test_collect_main_files_worker.py` | unit | MOVE_ONLY | 19 | tests/unit/main_app/jobs_workers/test_collect_main_files_worker.py |
| `tests/main_app/jobs_workers/test_download_main_files_worker.py` | unit | MOVE_ONLY | 33 | tests/unit/main_app/jobs_workers/test_download_main_files_worker.py |
| `tests/main_app/jobs_workers/test_fix_nested_main_files_worker.py` | unit | MOVE_ONLY | 14 | tests/unit/main_app/jobs_workers/test_fix_nested_main_files_worker.py |
| `tests/main_app/jobs_workers/test_jobs_worker.py` | unit | MOVE_ONLY | 8 | tests/unit/main_app/jobs_workers/test_jobs_worker.py |
| `tests/main_app/jobs_workers/test_worker_cancellation.py` | unit | MOVE_ONLY | 3 | tests/unit/main_app/jobs_workers/test_worker_cancellation.py |
| `tests/main_app/jobs_workers/utils/test_add_svglanguages_template_utils.py` | unit | MOVE_ONLY | 22 | tests/unit/main_app/jobs_workers/utils/test_add_svglanguages_template_utils.py |
| `tests/main_app/jobs_workers/utils/test_crop_main_files_utils.py` | unit | MOVE_ONLY | 9 | tests/unit/main_app/jobs_workers/utils/test_crop_main_files_utils.py |
| `tests/main_app/jobs_workers/utils/test_jobs_workers_utils.py` | unit | MOVE_ONLY | 6 | tests/unit/main_app/jobs_workers/utils/test_jobs_workers_utils.py |
| `tests/main_app/public_jobs_workers/copy_svg_langs/test_copy_svg_langs_processor.py` | unit | MOVE_ONLY | 8 | tests/unit/main_app/public_jobs_workers/copy_svg_langs/test_copy_svg_langs_processor.py |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_extracts_task.py` | unit | MOVE_ONLY | 1 | tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_extracts_task.py |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_fix_nested_tasks.py` | unit | MOVE_ONLY | 2 | tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_fix_nested_tasks.py |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_inject_tasks.py` | unit | MOVE_ONLY | 2 | tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_inject_tasks.py |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_start_bot.py` | unit | MOVE_ONLY | 2 | tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_start_bot.py |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_bot.py` | unit | MOVE_ONLY | 2 | tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_bot.py |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_tasks.py` | unit | MOVE_ONLY | 4 | tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_tasks.py |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_up.py` | unit | MOVE_ONLY | 3 | tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_up.py |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/test_legacy_threads.py` | N/A | DELETE | 0 | N/A |
| `tests/main_app/public_jobs_workers/copy_svg_langs_legacy/test_legacy_worker.py` | N/A | DELETE | 0 | N/A |
| `tests/main_app/services/test_admin_service.py` | unit | MOVE_ONLY | 8 | tests/unit/main_app/services/test_admin_service.py |
| `tests/main_app/services/test_jobs_service.py` | unit | MOVE_ONLY | 25 | tests/unit/main_app/services/test_jobs_service.py |
| `tests/main_app/services/test_owid_charts_service.py` | unit | MOVE_ONLY | 13 | tests/unit/main_app/services/test_owid_charts_service.py |
| `tests/main_app/services/test_template_service.py` | unit | MOVE_ONLY | 11 | tests/unit/main_app/services/test_template_service.py |
| `tests/main_app/users/test_current_unit.py` | mixed | SPLIT | 4 | unit(2) + integration(2) |
| `tests/main_app/users/test_store.py` | unit | MOVE_ONLY | 23 | tests/unit/main_app/db/test_user_tokens.py |
| `tests/main_app/users/test_users_store.py` | unit | MOVE_ONLY | 2 | tests/unit/main_app/db/test_users_store.py |
| `tests/main_app/utils/api_services_utils/test_download_file_utils.py` | unit | MOVE_ONLY | 9 | tests/unit/main_app/utils/api_services_utils/test_download_file_utils.py |
| `tests/main_app/utils/categories_utils/test_capitalize_category.py` | unit | MOVE_ONLY | 13 | tests/unit/main_app/utils/categories_utils/test_capitalize_category.py |
| `tests/main_app/utils/categories_utils/test_categories_utils.py` | unit | MOVE_ONLY | 2 | tests/unit/main_app/utils/categories_utils/test_categories_utils.py |
| `tests/main_app/utils/categories_utils/test_extract_categories.py` | unit | MOVE_ONLY | 9 | tests/unit/main_app/utils/categories_utils/test_extract_categories.py |
| `tests/main_app/utils/categories_utils/test_find_missing_categories.py` | unit | MOVE_ONLY | 11 | tests/unit/main_app/utils/categories_utils/test_find_missing_categories.py |
| `tests/main_app/utils/categories_utils/test_merge_categories.py` | unit | MOVE_ONLY | 10 | tests/unit/main_app/utils/categories_utils/test_merge_categories.py |
| `tests/main_app/utils/test_jinja_filters.py` | unit | MOVE_ONLY | 12 | tests/unit/main_app/utils/test_jinja_filters.py |
| `tests/main_app/utils/test_verify.py` | unit | MOVE_ONLY | 11 | tests/unit/main_app/utils/test_verify.py |
| `tests/main_app/utils/wikitext/temps_bot/test_get_files_list.py` | unit | MOVE_ONLY | 3 | tests/unit/main_app/utils/wikitext/temps_bot/test_get_files_list.py |
| `tests/main_app/utils/wikitext/temps_bot/test_get_titles.py` | unit | MOVE_ONLY | 4 | tests/unit/main_app/utils/wikitext/temps_bot/test_get_titles.py |
| `tests/main_app/utils/wikitext/temps_bot/test_temps_bot.py` | unit | MOVE_ONLY | 22 | tests/unit/main_app/utils/wikitext/temps_bot/test_temps_bot.py |
| `tests/main_app/utils/wikitext/test_appendImageExtractedTemplate.py` | unit | MOVE_ONLY | 1 | tests/unit/main_app/utils/wikitext/test_appendImageExtractedTemplate.py |
| `tests/main_app/utils/wikitext/test_before_methods.py` | unit | MOVE_ONLY | 1 | tests/unit/main_app/utils/wikitext/test_before_methods.py |
| `tests/main_app/utils/wikitext/test_files_text.py` | unit | MOVE_ONLY | 22 | tests/unit/main_app/utils/wikitext/test_files_text.py |
| `tests/main_app/utils/wikitext/test_other_versions.py` | unit | MOVE_ONLY | 4 | tests/unit/main_app/utils/wikitext/test_other_versions.py |
| `tests/main_app/utils/wikitext/test_temp_source.py` | unit | MOVE_ONLY | 32 | tests/unit/main_app/utils/wikitext/test_temp_source.py |
| `tests/main_app/utils/wikitext/test_template_page.py` | unit | MOVE_ONLY | 10 | tests/unit/main_app/utils/wikitext/test_template_page.py |
| `tests/main_app/utils/wikitext/test_text_utils.py` | unit | MOVE_ONLY | 5 | tests/unit/main_app/utils/wikitext/test_text_utils.py |
| `tests/main_app/utils/wikitext/test_update_original_file_text.py` | unit | MOVE_ONLY | 22 | tests/unit/main_app/utils/wikitext/test_update_original_file_text.py |
| `tests/main_app/utils/wikitext/test_update_template_page_file_reference.py` | unit | MOVE_ONLY | 5 | tests/unit/main_app/utils/wikitext/test_update_template_page_file_reference.py |
| `tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py` | unit | MOVE_ONLY | 23 | tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py |
| `tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py` | unit | MOVE_ONLY | 18 | tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py |
| `tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py` | unit | MOVE_ONLY | 4 | tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py |
| `tests/main_app/utils/wikitext/titles_utils/test_find_main_title.py` | unit | MOVE_ONLY | 12 | tests/unit/main_app/utils/wikitext/titles_utils/test_find_main_title.py |
| `tests/main_app/utils/wikitext/titles_utils/test_last_world_file_with_full_date.py` | unit | MOVE_ONLY | 22 | tests/unit/main_app/utils/wikitext/titles_utils/test_last_world_file_with_full_date.py |
| `tests/main_app/utils/wikitext/titles_utils/test_main_file.py` | unit | MOVE_ONLY | 28 | tests/unit/main_app/utils/wikitext/titles_utils/test_main_file.py |
| `tests/main_app/utils/wikitext/titles_utils/test_match_main_title.py` | unit | MOVE_ONLY | 10 | tests/unit/main_app/utils/wikitext/titles_utils/test_match_main_title.py |
| `tests/main_app/test_init.py` | integration | MOVE_ONLY | 8 | tests/integration/main_app/test_app_factory.py |
| `tests/main_app/test_app_factory.py` | mixed | SPLIT | 14 | unit(6) + integration(8) |
| `tests/main_app/test_config.py` | unit | MOVE_ONLY | 21 | tests/unit/main_app/test_config.py |
| `tests/main_app/test_data.py` | unit | MOVE_ONLY | 1 | tests/unit/main_app/test_data.py |

## Files Requiring Split

### `tests/main_app/app_routes/auth/test_auth_oauth_helpers.py`
- **Unit destination**: `tests/unit/main_app/app_routes/auth/test_auth_oauth_helpers_unit.py`
  - Tests: test_complete_login_returns_access_and_identity, test_complete_login_raises_identity_error
- **Integration destination**: `tests/integration/main_app/app_routes/auth/test_auth_oauth_helpers.py`
  - Tests: test_start_login_returns_redirect_and_request_token

### `tests/main_app/users/test_current_unit.py`
- **Unit destination**: `tests/unit/main_app/services/test_users_service_unit.py`
  - Tests: test_context_user, test_CurrentUser
- **Integration destination**: `tests/integration/main_app/services/test_users_service.py`
  - Tests: test_resolve_user_id, test_current_user

### `tests/main_app/test_app_factory.py`
- **Unit destination**: `tests/unit/main_app/test_app_factory_regression_unit.py`
  - Tests: test_format_stage_timestamp_valid, test_format_stage_timestamp_empty, test_format_stage_timestamp_invalid, test_format_stage_timestamp_afternoon, test_format_stage_timestamp_noon, test_format_stage_timestamp_midnight
- **Integration destination**: `tests/integration/main_app/test_app_factory_regression.py`
  - Tests: test_create_app_does_not_touch_mysql_when_unconfigured, test_create_app_registers_blueprints, test_create_app_sets_secret_key, test_create_app_configures_cookie_settings, test_create_app_registers_context_processor, test_create_app_registers_error_handlers, test_create_app_strict_slashes_disabled, test_create_app_jinja_env_configured

## Git Commands

```bash
# Move files (MOVE_ONLY)
git mv tests/main_app/admins/test_admins_required.py tests/unit/main_app/app_routes/admin/test_admins_required.py
git mv tests/main_app/api_services/clients/test_commons_client.py tests/unit/main_app/api_services/clients/test_commons_client.py
git mv tests/main_app/api_services/clients/test_wiki_client.py tests/unit/main_app/api_services/clients/test_wiki_client.py
git mv tests/main_app/api_services/mwclient_page/test_mwclient_page.py tests/unit/main_app/api_services/test_mwclient_page.py
git mv tests/main_app/api_services/mwclient_page/test_mwclient_page2.py tests/unit/main_app/api_services/test_mwclient_page2.py
git mv tests/main_app/api_services/test_category.py tests/unit/main_app/api_services/test_category.py
git mv tests/main_app/api_services/test_pages_api.py tests/unit/main_app/api_services/test_pages_api.py
git mv tests/main_app/api_services/test_text_api.py tests/unit/main_app/api_services/test_text_api.py
git mv tests/main_app/api_services/test_text_bot.py tests/unit/main_app/api_services/test_text_bot.py
git mv tests/main_app/api_services/test_upload_bot.py tests/unit/main_app/api_services/test_upload_bot.py
git mv tests/main_app/api_services/test_upload_bot_new.py tests/unit/main_app/api_services/test_upload_bot_new.py
git mv tests/main_app/app_routes/admin/admin_routes/test_coordinators_exception_handling.py tests/unit/main_app/app_routes/app_routes/admin_routes/test_coordinators_exception_handling.py
git mv tests/main_app/app_routes/admin/test_sidebar.py tests/unit/main_app/app_routes/admin/test_sidebar.py
git mv tests/main_app/app_routes/auth/test_auth_cookie.py tests/unit/main_app/app_routes/auth/test_auth_cookie.py
git mv tests/main_app/app_routes/auth/test_cookie.py tests/unit/main_app/app_routes/auth/test_cookie.py
git mv tests/main_app/app_routes/auth/test_oauth.py tests/unit/main_app/app_routes/auth/test_oauth.py
git mv tests/main_app/app_routes/auth/test_rate_limit.py tests/unit/main_app/app_routes/auth/test_rate_limit.py
git mv tests/main_app/app_routes/fix_nested/test_explorer_routes_undo.py tests/unit/main_app/app_routes/fix_nested/test_explorer_routes_undo.py
git mv tests/main_app/app_routes/fix_nested/test_fix_nested_routes_unit.py tests/unit/main_app/app_routes/fix_nested/test_fix_nested_routes_unit.py
git mv tests/main_app/app_routes/fix_nested/test_fix_nested_worker.py tests/unit/main_app/app_routes/fix_nested/test_fix_nested_worker.py
git mv tests/main_app/app_routes/utils/test_args_utils.py tests/unit/main_app/app_routes/utils/test_args_utils.py
git mv tests/main_app/app_routes/utils/test_compare.py tests/unit/main_app/app_routes/utils/test_compare.py
git mv tests/main_app/app_routes/utils/test_explorer_utils.py tests/unit/main_app/app_routes/utils/test_explorer_utils.py
git mv tests/main_app/app_routes/utils/test_fix_nested_utils.py tests/unit/main_app/app_routes/utils/test_fix_nested_utils.py
git mv tests/main_app/app_routes/utils/test_routes_utils_unit.py tests/unit/main_app/app_routes/utils/test_routes_utils.py
git mv tests/main_app/app_routes/utils/test_thumbnail_utils.py tests/unit/main_app/app_routes/utils/test_thumbnail_utils.py
git mv tests/main_app/core/test_crypto.py tests/unit/main_app/core/test_crypto.py
git mv tests/main_app/db/test_db_class.py tests/unit/main_app/db/test_db_class.py
git mv tests/main_app/db/test_db_CoordinatorsDB.py tests/unit/main_app/db/test_db_CoordinatorsDB.py
git mv tests/main_app/db/test_db_Jobs.py tests/unit/main_app/db/test_db_Jobs.py
git mv tests/main_app/db/test_db_OwidCharts.py tests/unit/main_app/db/test_db_OwidCharts.py
git mv tests/main_app/db/test_db_Settings.py tests/unit/main_app/db/test_db_Settings.py
git mv tests/main_app/db/test_db_Templates.py tests/unit/main_app/db/test_db_Templates.py
git mv tests/main_app/db/test_exceptions.py tests/unit/main_app/db/test_exceptions.py
git mv tests/main_app/db/test_fix_nested_task_store.py tests/unit/main_app/db/test_fix_nested_task_store.py
git mv tests/main_app/db/test_svg_db.py tests/unit/main_app/db/test_svg_db.py
git mv tests/main_app/jobs_workers/add_svglanguages_template/test_add_svglanguages_template_worker.py tests/unit/main_app/jobs_workers/add_svglanguages_template/test_add_svglanguages_template_worker.py
git mv tests/main_app/jobs_workers/create_owid_pages/test_create_owid_pages_worker.py tests/unit/main_app/jobs_workers/create_owid_pages/test_create_owid_pages_worker.py
git mv tests/main_app/jobs_workers/create_owid_pages/test_owid_template_converter.py tests/unit/main_app/jobs_workers/create_owid_pages/test_owid_template_converter.py
git mv tests/main_app/jobs_workers/crop_main_files/test_crop_file.py tests/unit/main_app/jobs_workers/crop_main_files/test_crop_file.py
git mv tests/main_app/jobs_workers/crop_main_files/test_crop_main_files_worker.py tests/unit/main_app/jobs_workers/crop_main_files/test_crop_main_files_worker.py
git mv tests/main_app/jobs_workers/crop_main_files/test_download.py tests/unit/main_app/jobs_workers/crop_main_files/test_download.py
git mv tests/main_app/jobs_workers/crop_main_files/test_process_new.py tests/unit/main_app/jobs_workers/crop_main_files/test_process_new.py
git mv tests/main_app/jobs_workers/crop_main_files/test_upload.py tests/unit/main_app/jobs_workers/crop_main_files/test_upload.py
git mv tests/main_app/jobs_workers/test_base_worker.py tests/unit/main_app/jobs_workers/test_base_worker.py
git mv tests/main_app/jobs_workers/test_collect_main_files_worker.py tests/unit/main_app/jobs_workers/test_collect_main_files_worker.py
git mv tests/main_app/jobs_workers/test_download_main_files_worker.py tests/unit/main_app/jobs_workers/test_download_main_files_worker.py
git mv tests/main_app/jobs_workers/test_fix_nested_main_files_worker.py tests/unit/main_app/jobs_workers/test_fix_nested_main_files_worker.py
git mv tests/main_app/jobs_workers/test_jobs_worker.py tests/unit/main_app/jobs_workers/test_jobs_worker.py
git mv tests/main_app/jobs_workers/test_worker_cancellation.py tests/unit/main_app/jobs_workers/test_worker_cancellation.py
git mv tests/main_app/jobs_workers/utils/test_add_svglanguages_template_utils.py tests/unit/main_app/jobs_workers/utils/test_add_svglanguages_template_utils.py
git mv tests/main_app/jobs_workers/utils/test_crop_main_files_utils.py tests/unit/main_app/jobs_workers/utils/test_crop_main_files_utils.py
git mv tests/main_app/jobs_workers/utils/test_jobs_workers_utils.py tests/unit/main_app/jobs_workers/utils/test_jobs_workers_utils.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs/test_copy_svg_langs_processor.py tests/unit/main_app/public_jobs_workers/copy_svg_langs/test_copy_svg_langs_processor.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_extracts_task.py tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_extracts_task.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_fix_nested_tasks.py tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_fix_nested_tasks.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_inject_tasks.py tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_inject_tasks.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_start_bot.py tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_start_bot.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_bot.py tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_bot.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_tasks.py tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_tasks.py
git mv tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_up.py tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_up.py
git mv tests/main_app/services/test_admin_service.py tests/unit/main_app/services/test_admin_service.py
git mv tests/main_app/services/test_jobs_service.py tests/unit/main_app/services/test_jobs_service.py
git mv tests/main_app/services/test_owid_charts_service.py tests/unit/main_app/services/test_owid_charts_service.py
git mv tests/main_app/services/test_template_service.py tests/unit/main_app/services/test_template_service.py
git mv tests/main_app/users/test_store.py tests/unit/main_app/db/test_user_tokens.py
git mv tests/main_app/users/test_users_store.py tests/unit/main_app/db/test_users_store.py
git mv tests/main_app/utils/api_services_utils/test_download_file_utils.py tests/unit/main_app/utils/api_services_utils/test_download_file_utils.py
git mv tests/main_app/utils/categories_utils/test_capitalize_category.py tests/unit/main_app/utils/categories_utils/test_capitalize_category.py
git mv tests/main_app/utils/categories_utils/test_categories_utils.py tests/unit/main_app/utils/categories_utils/test_categories_utils.py
git mv tests/main_app/utils/categories_utils/test_extract_categories.py tests/unit/main_app/utils/categories_utils/test_extract_categories.py
git mv tests/main_app/utils/categories_utils/test_find_missing_categories.py tests/unit/main_app/utils/categories_utils/test_find_missing_categories.py
git mv tests/main_app/utils/categories_utils/test_merge_categories.py tests/unit/main_app/utils/categories_utils/test_merge_categories.py
git mv tests/main_app/utils/test_jinja_filters.py tests/unit/main_app/utils/test_jinja_filters.py
git mv tests/main_app/utils/test_verify.py tests/unit/main_app/utils/test_verify.py
git mv tests/main_app/utils/wikitext/temps_bot/test_get_files_list.py tests/unit/main_app/utils/wikitext/temps_bot/test_get_files_list.py
git mv tests/main_app/utils/wikitext/temps_bot/test_get_titles.py tests/unit/main_app/utils/wikitext/temps_bot/test_get_titles.py
git mv tests/main_app/utils/wikitext/temps_bot/test_temps_bot.py tests/unit/main_app/utils/wikitext/temps_bot/test_temps_bot.py
git mv tests/main_app/utils/wikitext/test_appendImageExtractedTemplate.py tests/unit/main_app/utils/wikitext/test_appendImageExtractedTemplate.py
git mv tests/main_app/utils/wikitext/test_before_methods.py tests/unit/main_app/utils/wikitext/test_before_methods.py
git mv tests/main_app/utils/wikitext/test_files_text.py tests/unit/main_app/utils/wikitext/test_files_text.py
git mv tests/main_app/utils/wikitext/test_other_versions.py tests/unit/main_app/utils/wikitext/test_other_versions.py
git mv tests/main_app/utils/wikitext/test_temp_source.py tests/unit/main_app/utils/wikitext/test_temp_source.py
git mv tests/main_app/utils/wikitext/test_template_page.py tests/unit/main_app/utils/wikitext/test_template_page.py
git mv tests/main_app/utils/wikitext/test_text_utils.py tests/unit/main_app/utils/wikitext/test_text_utils.py
git mv tests/main_app/utils/wikitext/test_update_original_file_text.py tests/unit/main_app/utils/wikitext/test_update_original_file_text.py
git mv tests/main_app/utils/wikitext/test_update_template_page_file_reference.py tests/unit/main_app/utils/wikitext/test_update_template_page_file_reference.py
git mv tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py
git mv tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py
git mv tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py
git mv tests/main_app/utils/wikitext/titles_utils/test_find_main_title.py tests/unit/main_app/utils/wikitext/titles_utils/test_find_main_title.py
git mv tests/main_app/utils/wikitext/titles_utils/test_last_world_file_with_full_date.py tests/unit/main_app/utils/wikitext/titles_utils/test_last_world_file_with_full_date.py
git mv tests/main_app/utils/wikitext/titles_utils/test_main_file.py tests/unit/main_app/utils/wikitext/titles_utils/test_main_file.py
git mv tests/main_app/utils/wikitext/titles_utils/test_match_main_title.py tests/unit/main_app/utils/wikitext/titles_utils/test_match_main_title.py
git mv tests/main_app/test_init.py tests/integration/main_app/test_app_factory.py
git mv tests/main_app/test_config.py tests/unit/main_app/test_config.py
git mv tests/main_app/test_data.py tests/unit/main_app/test_data.py

# Split files — create new files, then delete old
# Processing tests/main_app/app_routes/auth/test_auth_oauth_helpers.py
cp tests/main_app/app_routes/auth/test_auth_oauth_helpers.py tests/integration/main_app/app_routes/auth/test_auth_oauth_helpers.py
cp tests/main_app/app_routes/auth/test_auth_oauth_helpers.py tests/unit/main_app/app_routes/auth/test_auth_oauth_helpers_unit.py
git rm tests/main_app/app_routes/auth/test_auth_oauth_helpers.py
# Processing tests/main_app/users/test_current_unit.py
cp tests/main_app/users/test_current_unit.py tests/integration/main_app/services/test_users_service.py
cp tests/main_app/users/test_current_unit.py tests/unit/main_app/services/test_users_service_unit.py
git rm tests/main_app/users/test_current_unit.py
# Processing tests/main_app/test_app_factory.py
cp tests/main_app/test_app_factory.py tests/integration/main_app/test_app_factory_regression.py
cp tests/main_app/test_app_factory.py tests/unit/main_app/test_app_factory_regression_unit.py
git rm tests/main_app/test_app_factory.py

# Delete placeholder files
git rm tests/main_app/public_jobs_workers/copy_svg_langs_legacy/test_legacy_threads.py
git rm tests/main_app/public_jobs_workers/copy_svg_langs_legacy/test_legacy_worker.py
```

## Full JSON Report

```json
{
    "tests/unit/main_app/app_routes/admin/test_admins_required.py": {
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
    "tests/main_app/admins/test_admins_required.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/api_services/clients/test_commons_client.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/api_services/clients/test_wiki_client.py": {
        "action": "CREATE",
        "source": "tests/main_app/api_services/clients/test_wiki_client.py",
        "tests": [
            "test_build_upload_site_uses_decrypted_tokens_and_consumer"
        ],
        "type": "unit"
    },
    "tests/main_app/api_services/clients/test_wiki_client.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/api_services/test_mwclient_page.py": {
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
    "tests/main_app/api_services/mwclient_page/test_mwclient_page.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/api_services/test_mwclient_page2.py": {
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
    "tests/main_app/api_services/mwclient_page/test_mwclient_page2.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/api_services/test_category.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/api_services/test_pages_api.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
            "test_with_prefixed_filename",
            "test_site_exception_returns_empty_string",
            "test_text_method_exception_returns_empty_string",
            "test_valid_inputs_returns_text",
            "test_does_not_add_file_prefix",
            "test_missing_page_name_returns_empty_string",
            "test_missing_site_returns_empty_string",
            "test_site_exception_returns_empty_string"
        ],
        "type": "unit"
    },
    "tests/main_app/api_services/test_text_api.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/api_services/test_text_bot.py": {
        "action": "CREATE",
        "source": "tests/main_app/api_services/test_text_bot.py",
        "tests": [
            "test_get_wikitext_success",
            "test_get_wikitext_not_found",
            "test_get_wikitext_error"
        ],
        "type": "unit"
    },
    "tests/main_app/api_services/test_text_bot.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/api_services/test_upload_bot.py": {
        "action": "CREATE",
        "source": "tests/main_app/api_services/test_upload_bot.py",
        "tests": [
            "test_upload_file_no_site",
            "test_upload_file_not_found_on_commons",
            "test_upload_file_not_found_on_server",
            "test_upload_file_success",
            "test_upload_file_fileexists_no_change"
        ],
        "type": "unit"
    },
    "tests/main_app/api_services/test_upload_bot.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/api_services/test_upload_bot_new.py": {
        "action": "CREATE",
        "source": "tests/main_app/api_services/test_upload_bot_new.py",
        "tests": [
            "test_strips_file_prefix_lowercase",
            "test_strips_file_prefix_uppercase",
            "test_strips_file_prefix_mixed_case",
            "test_strips_surrounding_whitespace",
            "test_no_prefix_unchanged",
            "test_none_file_name_not_processed",
            "test_no_site",
            "test_no_file_name",
            "test_no_file_path",
            "test_existing_file_mode_file_not_on_commons",
            "test_new_file_mode_file_already_on_commons",
            "test_file_not_on_server",
            "test_all_valid_existing_file",
            "test_all_valid_new_file",
            "test_success",
            "test_assert_user_failed",
            "test_user_blocked",
            "test_insufficient_permission",
            "test_file_exists",
            "test_maximum_retries_exceeded",
            "test_timeout",
            "test_connection_error",
            "test_http_error",
            "test_rate_limited",
            "test_fileexists_no_change",
            "test_other_api_error",
            "test_unexpected_exception",
            "test_succeeds_on_first_retry",
            "test_exhausts_all_retries",
            "test_sleeps_correct_delays",
            "test_stops_early_on_non_ratelimited_error",
            "test_succeeds_on_second_retry",
            "test_success",
            "test_check_kwargs_fails_early",
            "test_rate_limited_then_success",
            "test_rate_limited_exhausts_all_retries",
            "test_rate_limited_sleeps_correct_delays",
            "test_non_ratelimited_error_no_retry",
            "test_new_file_upload_success"
        ],
        "type": "unit"
    },
    "tests/main_app/api_services/test_upload_bot_new.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/app_routes/app_routes/admin_routes/test_coordinators_exception_handling.py": {
        "action": "CREATE",
        "source": "tests/main_app/app_routes/admin/admin_routes/test_coordinators_exception_handling.py",
        "tests": [
            "test_add_coordinator_catches_both_lookup_and_value_errors"
        ],
        "type": "unit"
    },
    "tests/main_app/app_routes/admin/admin_routes/test_coordinators_exception_handling.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
            "test_create_side_no_active_item",
            "test_create_side_with_active_item",
            "test_sidebar_contains_jobs_section",
            "test_sidebar_contains_collect_main_files_job_link",
            "test_sidebar_contains_fix_nested_main_files_job_link",
            "test_sidebar_marks_collect_main_files_as_active",
            "test_sidebar_marks_fix_nested_main_files_as_active"
        ],
        "type": "unit"
    },
    "tests/main_app/app_routes/admin/test_sidebar.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/app_routes/auth/test_auth_cookie.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/app_routes/auth/test_auth_oauth_helpers_unit.py": {
        "action": "CREATE",
        "source": "tests/main_app/app_routes/auth/test_auth_oauth_helpers.py",
        "tests": [
            "test_complete_login_returns_access_and_identity",
            "test_complete_login_raises_identity_error"
        ],
        "type": "unit"
    },
    "tests/integration/main_app/app_routes/auth/test_auth_oauth_helpers.py": {
        "action": "CREATE",
        "source": "tests/main_app/app_routes/auth/test_auth_oauth_helpers.py",
        "tests": [
            "test_start_login_returns_redirect_and_request_token"
        ],
        "type": "integration"
    },
    "tests/main_app/app_routes/auth/test_auth_oauth_helpers.py": {
        "action": "DELETE",
        "reason": "Split into unit and integration"
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
    "tests/main_app/app_routes/auth/test_cookie.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/app_routes/auth/test_oauth.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/app_routes/auth/test_rate_limit.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/app_routes/fix_nested/test_explorer_routes_undo.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/app_routes/fix_nested/test_fix_nested_routes_unit.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/app_routes/fix_nested/test_fix_nested_worker.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/app_routes/utils/test_args_utils.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/app_routes/utils/test_compare.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/app_routes/utils/test_explorer_utils.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/app_routes/utils/test_fix_nested_utils.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/app_routes/utils/test_routes_utils.py": {
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
    "tests/main_app/app_routes/utils/test_routes_utils_unit.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/app_routes/utils/test_thumbnail_utils.py": {
        "action": "CREATE",
        "source": "tests/main_app/app_routes/utils/test_thumbnail_utils.py",
        "tests": [
            "test_save_thumb_returns_false2"
        ],
        "type": "unit"
    },
    "tests/main_app/app_routes/utils/test_thumbnail_utils.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/core/test_crypto.py": {
        "action": "CREATE",
        "source": "tests/main_app/core/test_crypto.py",
        "tests": [
            "test_encrypt_decrypt_roundtrip"
        ],
        "type": "unit"
    },
    "tests/main_app/core/test_crypto.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/db/test_db_class.py": {
        "action": "CREATE",
        "source": "tests/main_app/db/test_db_class.py",
        "tests": [
            "test_Database_init_basic",
            "test_Database_connect",
            "test_Database_ensure_connection_new",
            "test_Database_ensure_connection_ping",
            "test_Database_close",
            "test_Database_context_manager",
            "test_Database_execute_query_success",
            "test_Database_fetch_query_success"
        ],
        "type": "unit"
    },
    "tests/main_app/db/test_db_class.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/db/test_db_CoordinatorsDB.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/db/test_db_Jobs.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/db/test_db_OwidCharts.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
            "test_update_setting_with_value_type_serializes_correctly",
            "test_serialize_value_none",
            "test_serialize_value_boolean",
            "test_serialize_value_integer",
            "test_serialize_value_json",
            "test_serialize_value_string"
        ],
        "type": "unit"
    },
    "tests/main_app/db/test_db_Settings.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/db/test_db_Templates.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/db/test_exceptions.py": {
        "action": "CREATE",
        "source": "tests/main_app/db/test_exceptions.py",
        "tests": [
            "test_MaxUserConnectionsError"
        ],
        "type": "unit"
    },
    "tests/main_app/db/test_exceptions.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/db/test_fix_nested_task_store.py": {
        "action": "CREATE",
        "source": "tests/main_app/db/test_fix_nested_task_store.py",
        "tests": [
            "test_init_schema",
            "test_create_task_success",
            "test_create_task_failure",
            "test_get_task_success",
            "test_get_task_json_error",
            "test_get_task_not_found",
            "test_update_status",
            "test_update_nested_counts",
            "test_update_download_result",
            "test_update_upload_result",
            "test_update_error",
            "test_list_tasks",
            "test_list_tasks_failure"
        ],
        "type": "unit"
    },
    "tests/main_app/db/test_fix_nested_task_store.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/db/test_svg_db.py": {
        "action": "CREATE",
        "source": "tests/main_app/db/test_svg_db.py",
        "tests": [
            "test_get_db",
            "test_close_cached_db",
            "test_execute_query",
            "test_fetch_query",
            "test_execute_query_safe",
            "test_fetch_query_safe"
        ],
        "type": "unit"
    },
    "tests/main_app/db/test_svg_db.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/jobs_workers/add_svglanguages_template/test_add_svglanguages_template_worker.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/jobs_workers/create_owid_pages/test_create_owid_pages_worker.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/jobs_workers/create_owid_pages/test_owid_template_converter.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/create_owid_pages/test_owid_template_converter.py",
        "tests": [
            "test_create_new_text"
        ],
        "type": "unit"
    },
    "tests/main_app/jobs_workers/create_owid_pages/test_owid_template_converter.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/jobs_workers/crop_main_files/test_crop_file.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/crop_main_files/test_crop_file.py",
        "tests": [
            "test_get_max_y_of_element_with_rect",
            "test_get_max_y_of_element_with_circle",
            "test_get_max_y_of_element_with_no_y_attrs",
            "test_get_max_y_of_element_with_units",
            "test_get_max_y_of_element_with_invalid_values",
            "test_get_max_y_of_element_with_negative_values",
            "test_remove_footer_and_adjust_height_success",
            "test_remove_footer_and_adjust_height_updates_viewbox",
            "test_remove_footer_and_adjust_height_no_footer",
            "test_remove_footer_and_adjust_height_custom_footer_id",
            "test_remove_footer_and_adjust_height_custom_padding",
            "test_remove_footer_removes_siblings_after_footer",
            "test_crop_svg_file_success",
            "test_crop_svg_file_no_footer",
            "test_crop_svg_file_invalid_input",
            "test_crop_svg_file_file_not_found",
            "test_crop_svg_file_exception_handling",
            "test_crop_svg_file_permission_error",
            "test_remove_footer_preserves_namespaces",
            "test_crop_svg_with_complex_nested_elements",
            "test_get_max_y_with_line_elements",
            "test_crop_svg_file_output_is_valid_xml"
        ],
        "type": "unit"
    },
    "tests/main_app/jobs_workers/crop_main_files/test_crop_file.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/jobs_workers/crop_main_files/test_crop_main_files_worker.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/crop_main_files/test_crop_main_files_worker.py",
        "tests": [
            "test_crop_main_files_for_templates_basic_flow",
            "test_crop_main_files_for_templates_initializes_result",
            "test_crop_main_files_for_templates_with_user",
            "test_crop_main_files_for_templates_with_cancel_event",
            "test_crop_main_files_for_templates_handles_exception",
            "test_crop_main_files_for_templates_sets_completed_timestamp",
            "test_crop_main_files_for_templates_saves_final_result",
            "test_crop_main_files_for_templates_updates_final_status",
            "test_crop_main_files_for_templates_handles_save_failure",
            "test_crop_main_files_for_templates_handles_status_update_failure",
            "test_crop_main_files_for_templates_generates_correct_result_file_name",
            "test_crop_main_files_for_templates_passes_result_file_to_process",
            "test_crop_main_files_for_templates_preserves_cancelled_status",
            "test_crop_main_files_for_templates_preserves_failed_status",
            "test_crop_main_files_for_templates_different_exception_types",
            "test_crop_main_files_for_templates_upload_files_flag",
            "test_crop_main_files_for_templates_multiple_jobs",
            "test_crop_main_files_for_templates_started_at_timestamp",
            "test_crop_main_files_for_templates_exception_includes_traceback_in_logs",
            "test_crop_main_files_for_templates_completed_status_default"
        ],
        "type": "unit"
    },
    "tests/main_app/jobs_workers/crop_main_files/test_crop_main_files_worker.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/jobs_workers/crop_main_files/test_download.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/jobs_workers/crop_main_files/test_process_new.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/crop_main_files/test_process_new.py",
        "tests": [
            "test_default_initialization",
            "test_to_dict",
            "test_to_dict_with_none_paths",
            "test_file_exists",
            "test_file_does_not_exist",
            "test_processor_initialization",
            "test_processor_default_upload_files",
            "test_before_run_success",
            "test_before_run_lookup_error",
            "test_before_run_no_site_auth",
            "test_load_templates_filters_by_last_world_file",
            "test_apply_limits_with_crop_newest_upload_limit",
            "test_apply_limits_with_dev_limit",
            "test_step_download_success",
            "test_step_download_failure",
            "test_step_download_exception",
            "test_step_crop_success",
            "test_step_crop_failure",
            "test_step_upload_success",
            "test_step_upload_file_exists",
            "test_step_upload_failure",
            "test_step_update_original_no_change",
            "test_step_update_original_with_update",
            "test_step_update_original_update_fails",
            "test_step_update_template_no_change",
            "test_step_update_template_with_update",
            "test_fail_updates_status_and_result",
            "test_skip_step_updates_step_status",
            "test_skip_upload_steps",
            "test_is_cancelled_with_event",
            "test_is_cancelled_with_global_check",
            "test_append_adds_to_result",
            "test_get_priority",
            "test_process_template_file_already_exists",
            "test_process_template_full_pipeline",
            "test_process_template_upload_disabled",
            "test_run_full_workflow",
            "test_run_before_run_fails",
            "test_entry_point_creates_processor_and_runs",
            "test_entry_point_with_cancel_event"
        ],
        "type": "unit"
    },
    "tests/main_app/jobs_workers/crop_main_files/test_process_new.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/jobs_workers/crop_main_files/test_upload.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/crop_main_files/test_upload.py",
        "tests": [
            "test_upload_cropped_file_success",
            "test_upload_cropped_file_no_site",
            "test_upload_cropped_file_exception_during_upload",
            "test_upload_cropped_file_strips_file_prefix",
            "test_upload_cropped_file_without_file_prefix",
            "test_upload_cropped_file_with_special_characters",
            "test_upload_cropped_file_uses_new_file_flag",
            "test_upload_cropped_file_uses_correct_summary",
            "test_upload_cropped_file_returns_filename_in_result",
            "test_upload_cropped_file_with_very_long_filename",
            "test_upload_cropped_file_upload_result_missing_keys",
            "test_upload_cropped_file_with_unicode_filename",
            "test_upload_cropped_file_passes_correct_site",
            "test_upload_cropped_file_with_path_object",
            "test_upload_cropped_file_empty_filename",
            "test_upload_cropped_file_with_wikitext",
            "test_upload_cropped_file_upload_fails"
        ],
        "type": "unit"
    },
    "tests/main_app/jobs_workers/crop_main_files/test_upload.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/jobs_workers/test_base_worker.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/test_base_worker.py",
        "tests": [
            "test_successful_function_returns_result",
            "test_exception_is_caught_and_logged",
            "test_exception_saves_error_details",
            "test_handles_lookup_error_when_saving",
            "test_handles_exception_when_saving_error_result",
            "test_handles_lookup_error_in_fallback_update",
            "test_worker_initialization",
            "test_successful_run",
            "test_failed_run",
            "test_is_cancelled",
            "test_before_run_returns_false_on_lookup_error",
            "test_handle_error",
            "test_after_run_handles_save_exception",
            "test_after_run_handles_lookup_error",
            "test_run_returns_early_when_before_run_fails"
        ],
        "type": "unit"
    },
    "tests/main_app/jobs_workers/test_base_worker.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/jobs_workers/test_collect_main_files_worker.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/test_collect_main_files_worker.py",
        "tests": [
            "test_collect_main_files_with_no_templates",
            "test_collect_main_files_skips_templates_with_main_file",
            "test_collect_main_files_updates_template_without_main_file",
            "test_collect_main_files_handles_missing_wikitext",
            "test_collect_main_files_handles_missing_main_title",
            "test_collect_main_files_handles_exception",
            "test_collect_main_files_processes_multiple_templates",
            "test_collect_main_files_adds_new_templates_from_category",
            "test_collect_main_files_handles_add_template_value_error",
            "test_collect_main_files_full_workflow_with_new_templates",
            "test_collect_main_files_with_last_world_file",
            "test_collect_main_files_cancellation_during_template_addition",
            "test_collect_main_files_cancellation_during_processing",
            "test_collect_main_files_progress_saving_frequency",
            "test_collect_main_files_only_last_world_file",
            "test_collect_main_files_template_with_existing_main_file_only",
            "test_collect_main_files_add_template_generic_exception",
            "test_worker_class_get_job_type",
            "test_worker_class_get_initial_result"
        ],
        "type": "unit"
    },
    "tests/main_app/jobs_workers/test_collect_main_files_worker.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/jobs_workers/test_download_main_files_worker.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/test_download_main_files_worker.py",
        "tests": [
            "test_download_file_from_commons_success",
            "test_download_file_from_commons_empty_filename",
            "test_download_file_from_commons_request_error",
            "test_download_file_from_commons_unexpected_error",
            "test_download_file_from_commons_creates_session_if_none",
            "test_download_main_files_with_no_templates",
            "test_download_main_files_skips_templates_without_main_file",
            "test_download_main_files_downloads_template_with_main_file",
            "test_download_main_files_handles_download_failure",
            "test_download_main_files_handles_exception",
            "test_download_main_files_processes_multiple_templates",
            "test_download_main_files_respects_cancellation",
            "test_download_main_files_handles_file_with_file_prefix",
            "test_download_main_files_checks_if_file_exists",
            "test_download_main_files_fatal_error_handling",
            "test_generate_main_files_zip_success",
            "test_generate_main_files_zip_no_files",
            "test_generate_main_files_zip_directory_not_exists",
            "test_generate_main_files_zip_excludes_self",
            "test_create_main_files_zip_success",
            "test_create_main_files_zip_not_found",
            "test_create_main_files_zip_directory_not_exists",
            "test_create_main_files_zip_empty_file",
            "test_create_main_files_zip_empty_directory",
            "test_create_main_files_zip_ignores_subdirectories",
            "test_download_main_files_saves_progress_periodically",
            "test_download_file_from_commons_url_encoding",
            "test_download_file_from_commons_http_error_404",
            "test_download_main_files_creates_output_directory",
            "test_download_main_files_handles_job_deletion_during_final_status_update",
            "test_download_file_from_commons_with_special_characters",
            "test_download_main_files_generates_zip_on_completion",
            "test_download_main_files_no_zip_on_failure"
        ],
        "type": "unit"
    },
    "tests/main_app/jobs_workers/test_download_main_files_worker.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/jobs_workers/test_fix_nested_main_files_worker.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/test_fix_nested_main_files_worker.py",
        "tests": [
            "test_fix_nested_main_files_with_no_templates",
            "test_fix_nested_main_files_skips_templates_without_main_file",
            "test_fix_nested_main_files_processes_template_with_main_file",
            "test_fix_nested_main_files_handles_failed_fix",
            "test_fix_nested_main_files_handles_exception",
            "test_fix_nested_main_files_processes_multiple_templates",
            "test_download_failure_returns_error",
            "test_no_nested_tags_found",
            "test_fix_nested_tags_failure",
            "test_verify_fix_shows_no_tags_fixed",
            "test_upload_failure",
            "test_successful_fix_and_upload",
            "test_fix_nested_worker_handles_cancelled_fix_result",
            "test_fix_nested_worker_handles_failed_fix_without_no_nested_tags"
        ],
        "type": "unit"
    },
    "tests/main_app/jobs_workers/test_fix_nested_main_files_worker.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/jobs_workers/test_jobs_worker.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/test_jobs_worker.py",
        "tests": [
            "test_start_collect_main_files_job",
            "test_start_fix_nested_main_files_job",
            "test_cancel_job",
            "test_cancel_nonexistent_job",
            "test_runner_calls_target_and_cleans_up",
            "test_start_download_main_files_job",
            "test_start_job_with_invalid_job_type",
            "test_multiple_jobs_can_be_cancelled_independently"
        ],
        "type": "unit"
    },
    "tests/main_app/jobs_workers/test_jobs_worker.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/jobs_workers/test_worker_cancellation.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/test_worker_cancellation.py",
        "tests": [
            "test_collect_main_files_worker_cancellation",
            "test_fix_nested_main_files_worker_cancellation",
            "test_worker_handles_deleted_job"
        ],
        "type": "unit"
    },
    "tests/main_app/jobs_workers/test_worker_cancellation.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/jobs_workers/utils/test_add_svglanguages_template_utils.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/utils/test_add_svglanguages_template_utils.py",
        "tests": [
            "test_extract_file_name_from_translate_link",
            "test_extract_file_name_with_spaces_in_url",
            "test_extract_file_name_with_extra_whitespace",
            "test_returns_none_when_no_translate_link",
            "test_returns_none_when_empty_text",
            "test_translate_link_with_typo",
            "test_translate_link_variations",
            "test_add_template_after_translate_link",
            "test_returns_original_text_when_no_translate_link",
            "test_adds_template_only_once",
            "test_template_added_with_proper_formatting",
            "test_matches_standard_svglanguages_template",
            "test_matches_with_spaces_around_pipe",
            "test_matches_case_insensitive",
            "test_does_not_match_other_templates",
            "test_matches_in_larger_text",
            "test_matches_standard_translate_link",
            "test_matches_with_extra_spaces",
            "test_matches_case_insensitive",
            "test_matches_translate_variations",
            "test_does_not_match_other_urls",
            "test_does_not_match_non_svgtranslate_domain"
        ],
        "type": "unit"
    },
    "tests/main_app/jobs_workers/utils/test_add_svglanguages_template_utils.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/jobs_workers/utils/test_crop_main_files_utils.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/utils/test_crop_main_files_utils.py",
        "tests": [
            "test_basic_filename_with_file_prefix",
            "test_basic_filename_without_file_prefix",
            "test_filename_with_spaces",
            "test_filename_with_multiple_dots",
            "test_filename_with_different_extension",
            "test_filename_without_extension",
            "test_filename_with_underscores",
            "test_empty_filename",
            "test_filename_with_only_file_prefix"
        ],
        "type": "unit"
    },
    "tests/main_app/jobs_workers/utils/test_crop_main_files_utils.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/jobs_workers/utils/test_jobs_workers_utils.py": {
        "action": "CREATE",
        "source": "tests/main_app/jobs_workers/utils/test_jobs_workers_utils.py",
        "tests": [
            "test_generate_result_file_name",
            "test_generate_result_file_name_basic",
            "test_generate_result_file_name_string_job_id",
            "test_generate_result_file_name_different_job_types",
            "test_generate_result_file_name_zero_job_id",
            "test_generate_result_file_name_empty_job_type"
        ],
        "type": "unit"
    },
    "tests/main_app/jobs_workers/utils/test_jobs_workers_utils.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/public_jobs_workers/copy_svg_langs/test_copy_svg_langs_processor.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_extracts_task.py": {
        "action": "CREATE",
        "source": "tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_extracts_task.py",
        "tests": [
            "test_translations_task_stops_on_failure"
        ],
        "type": "unit"
    },
    "tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_extracts_task.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_fix_nested_tasks.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_inject_tasks.py": {
        "action": "CREATE",
        "source": "tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_inject_tasks.py",
        "tests": [
            "test_inject_task_success",
            "test_inject_task_no_dir"
        ],
        "type": "unit"
    },
    "tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_inject_tasks.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_start_bot.py": {
        "action": "CREATE",
        "source": "tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_start_bot.py",
        "tests": [
            "test_text_task_success",
            "test_text_task_fail"
        ],
        "type": "unit"
    },
    "tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_start_bot.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_bot.py": {
        "action": "CREATE",
        "source": "tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_bot.py",
        "tests": [
            "test_titles_task_success",
            "test_titles_task_fail"
        ],
        "type": "unit"
    },
    "tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_bot.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_titles_tasks.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/public_jobs_workers/copy_svg_langs_legacy/steps/test_up.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/main_app/public_jobs_workers/copy_svg_langs_legacy/test_legacy_threads.py": {
        "action": "DELETE",
        "reason": "No test functions found"
    },
    "tests/main_app/public_jobs_workers/copy_svg_langs_legacy/test_legacy_worker.py": {
        "action": "DELETE",
        "reason": "Empty or placeholder file"
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
    "tests/main_app/services/test_admin_service.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/services/test_jobs_service.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
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
    "tests/main_app/services/test_owid_charts_service.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/services/test_template_service.py": {
        "action": "CREATE",
        "source": "tests/main_app/services/test_template_service.py",
        "tests": [
            "test_get_templates_db_requires_config",
            "test_get_templates_db_caches_store",
            "test_list_templates_empty",
            "test_add_template_success",
            "test_add_template_duplicate_raises_value_error",
            "test_add_template_empty_title_raises_value_error",
            "test_list_templates_returns_all",
            "test_delete_template_success",
            "test_delete_template_not_found_raises_lookup_error",
            "test_template_record_dataclass_with_none_main_file",
            "test_module_exports_all_functions"
        ],
        "type": "unit"
    },
    "tests/main_app/services/test_template_service.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/services/test_users_service_unit.py": {
        "action": "CREATE",
        "source": "tests/main_app/users/test_current_unit.py",
        "tests": [
            "test_context_user",
            "test_CurrentUser"
        ],
        "type": "unit"
    },
    "tests/integration/main_app/services/test_users_service.py": {
        "action": "CREATE",
        "source": "tests/main_app/users/test_current_unit.py",
        "tests": [
            "test_resolve_user_id",
            "test_current_user"
        ],
        "type": "integration"
    },
    "tests/main_app/users/test_current_unit.py": {
        "action": "DELETE",
        "reason": "Split into unit and integration"
    },
    "tests/unit/main_app/db/test_user_tokens.py": {
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
    "tests/main_app/users/test_store.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/db/test_users_store.py": {
        "action": "CREATE",
        "source": "tests/main_app/users/test_users_store.py",
        "tests": [
            "test_mark_token_used_updates_last_used",
            "test_user_token_record_decrypted_marks_usage"
        ],
        "type": "unit"
    },
    "tests/main_app/users/test_users_store.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/api_services_utils/test_download_file_utils.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/api_services_utils/test_download_file_utils.py",
        "tests": [
            "test_download_single_file",
            "test_download_multiple_files",
            "test_download_skips_existing_files",
            "test_download_handles_network_error",
            "test_download_handles_404_error",
            "test_download_empty_list",
            "test_download_with_special_characters_in_filename",
            "test_download_with_unicode_filename",
            "test_download_timeout_handling"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/api_services_utils/test_download_file_utils.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/categories_utils/test_capitalize_category.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/categories_utils/test_capitalize_category.py",
        "tests": [
            "test_capitalize_category",
            "test_simple_category",
            "test_category_with_spaces",
            "test_category_with_special_chars",
            "test_single_part_category",
            "test_empty_parts",
            "test_empty_string",
            "test_multiple_colons",
            "test_single_character_parts",
            "test_uppercase_input",
            "test_mixed_case_input",
            "test_numeric_parts",
            "test_unicode_chars"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/categories_utils/test_capitalize_category.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/categories_utils/test_categories_utils.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/categories_utils/test_categories_utils.py",
        "tests": [
            "test_full_pipeline",
            "test_full_pipeline_2"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/categories_utils/test_categories_utils.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/categories_utils/test_extract_categories.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/categories_utils/test_extract_categories.py",
        "tests": [
            "test_extract_categories",
            "test_single_category",
            "test_multiple_categories",
            "test_ignore_non_category_links",
            "test_strip_whitespace",
            "test_no_categories",
            "test_extract_category_with_underscore",
            "test_extract_multiple_special_categories",
            "test_extract_mixed_normal_and_special_categories"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/categories_utils/test_extract_categories.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/categories_utils/test_find_missing_categories.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/categories_utils/test_find_missing_categories.py",
        "tests": [
            "test_old_category_not_in_new",
            "test_category_exists_in_both",
            "test_multiple_categories",
            "test_whitespace_ignored",
            "test_empty_old",
            "test_empty_new",
            "test_both_empty",
            "test_old_has_special_new_missing",
            "test_old_has_special_new_present",
            "test_special_chars_case_insensitive_matching",
            "test_multiple_missing_with_underscores"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/categories_utils/test_find_missing_categories.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/categories_utils/test_merge_categories.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/categories_utils/test_merge_categories.py",
        "tests": [
            "test_add_special_category_missing",
            "test_do_not_duplicate_special_category",
            "test_add_multiple_special_categories",
            "test_preserve_special_chars_formatting",
            "test_long_category_name_with_underscores",
            "test_underscore_at_end_of_name",
            "test_add_missing_category",
            "test_do_not_duplicate",
            "test_multiple_categories",
            "test_no_categories_anywhere"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/categories_utils/test_merge_categories.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/test_jinja_filters.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/test_jinja_filters.py",
        "tests": [
            "test_format_stage_timestamp_valid",
            "test_format_stage_timestamp_afternoon",
            "test_format_stage_timestamp_midnight",
            "test_format_stage_timestamp_noon",
            "test_format_stage_timestamp_empty_string",
            "test_format_stage_timestamp_none",
            "test_format_stage_timestamp_invalid_format",
            "test_format_stage_timestamp_with_microseconds",
            "test_format_stage_timestamp_different_months",
            "test_format_stage_timestamp_edge_time_values",
            "test_short_url_various",
            "test_short_url_exception_handling"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/test_jinja_filters.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/test_verify.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/test_verify.py",
        "tests": [
            "test_all_fields_present",
            "test_empty_fields_list",
            "test_single_missing_field",
            "test_multiple_missing_fields",
            "test_empty_string_considered_missing",
            "test_empty_list_considered_missing",
            "test_zero_considered_missing",
            "test_false_considered_missing",
            "test_whitespace_not_considered_missing",
            "test_logs_error_for_missing_fields",
            "test_logs_multiple_errors"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/test_verify.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/wikitext/temps_bot/test_get_files_list.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/temps_bot/test_get_files_list.py",
        "tests": [
            "test_get_files_list_prefers_svglanguages",
            "test_get_files_list_falls_back_to_translate",
            "test_get_files_list_no_titles_no_main"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/wikitext/temps_bot/test_get_files_list.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/wikitext/temps_bot/test_get_titles.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/temps_bot/test_get_titles.py",
        "tests": [
            "test_get_titles_from_sample_prompt",
            "test_get_titles_multiple_blocks_and_duplicates",
            "test_get_titles_empty_when_no_entries",
            "test_get_titles_regex_variants"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/wikitext/temps_bot/test_get_titles.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/wikitext/temps_bot/test_temps_bot.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/temps_bot/test_temps_bot.py",
        "tests": [
            "test_get_titles_from_wikilinks",
            "test_extract_single_file_link",
            "test_extract_multiple_file_links",
            "test_extract_file_link_with_spaces",
            "test_non_file_links_ignored",
            "test_empty_text",
            "test_no_file_links",
            "test_file_link_without_extension_ignored",
            "test_mixed_file_extensions",
            "test_extract_from_owidslidersrcs",
            "test_filter_duplicates",
            "test_no_duplicates_filtering",
            "test_empty_text",
            "test_no_owidslidersrcs_template",
            "test_case_insensitive_template_name",
            "test_multiple_owidslidersrcs_templates",
            "test_extract_main_title_and_titles",
            "test_main_title_underscores_to_spaces",
            "test_filter_duplicates",
            "test_empty_text",
            "test_no_main_title",
            "test_combined_wikilinks_and_owidslidersrcs"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/wikitext/temps_bot/test_temps_bot.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/wikitext/test_appendImageExtractedTemplate.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/test_appendImageExtractedTemplate.py",
        "tests": [
            "testItAppendsToExistingImageExtractedTemplate"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/wikitext/test_appendImageExtractedTemplate.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/wikitext/test_before_methods.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/test_before_methods.py",
        "tests": [
            "test_insert_before_license_header"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/wikitext/test_before_methods.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/wikitext/test_files_text.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/test_files_text.py",
        "tests": [
            "test_append_to_existing_template",
            "test_file_already_exists_in_text",
            "test_file_already_exists_case_insensitive",
            "test_file_already_exists_with_underscores",
            "test_no_template_returns_original",
            "test_template_variations_image_extracted",
            "test_template_variations_extracted_image",
            "test_template_variations_cropped_version",
            "test_template_with_spaces",
            "test_file_name_with_file_prefix",
            "test_empty_text",
            "test_file_already_in_text",
            "test_file_already_in_text_case_insensitive",
            "test_adds_image_extracted_template",
            "test_file_prefix_removed",
            "test_underscores_replaced_with_spaces",
            "test_empty_text",
            "test_add_extracted_from_template",
            "test_empty_text",
            "test_file_prefix_removed",
            "test_template_added_to_existing_content",
            "test_fallback_to_insert_before_methods"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/wikitext/test_files_text.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/wikitext/test_other_versions.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/test_other_versions.py",
        "tests": [
            "test_add_other_versions_to_information_template",
            "test_add_other_versions_with_extracted_from_template",
            "test_no_information_template_returns_original",
            "test_add_other_versions_preserves_template_structure"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/wikitext/test_other_versions.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/wikitext/test_temp_source.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/test_temp_source.py",
        "tests": [
            "test_basic",
            "test_with_www",
            "test_http_scheme",
            "test_trailing_characters",
            "test_extra_spaces",
            "test_case_insensitive_source",
            "test_multiple_lines",
            "test_invalid_domain",
            "test_missing_source",
            "test_with_wikilink_brackets",
            "test_basic_http",
            "test_https",
            "test_with_www",
            "test_spaces_before_star",
            "test_spaces_after_star",
            "test_wikilink_brackets",
            "test_trailing_characters",
            "test_invalid_domain",
            "test_no_url",
            "test_url_not_first_in_line",
            "test_multiple_lines",
            "test_valid_ourworldindata_url",
            "test_valid_www_ourworldindata_url",
            "test_invalid_domain",
            "test_invalid_url_raises_value_error",
            "test_case_insensitive_netloc",
            "test_fallback_to_second_method",
            "test_both_methods_fail_returns_empty",
            "test_first_method_succeeds",
            "test_check_url_false_in_find_template_source",
            "test_check_url_false_in_find_template_source_2",
            "test_urlparse_value_error_in_check_url"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/wikitext/test_temp_source.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/wikitext/test_template_page.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/test_template_page.py",
        "tests": [
            "test_replace_file_reference_basic",
            "test_replace_file_reference_with_file_prefix",
            "test_replace_multiple_file_references",
            "test_replace_in_syntaxhighlight_block",
            "test_no_file_reference",
            "test_empty_text",
            "test_partial_match_not_replaced",
            "test_different_file_not_replaced",
            "test_mixed_case_file_names",
            "test_file_reference_with_multiple_parameters"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/wikitext/test_template_page.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/wikitext/test_text_utils.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/test_text_utils.py",
        "tests": [
            "test_adds_prefix_when_missing",
            "test_does_not_add_prefix_when_present",
            "test_handles_empty_string",
            "test_handles_prefix_with_different_case",
            "test_handles_prefix_in_middle"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/wikitext/test_text_utils.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/wikitext/test_update_original_file_text.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/test_update_original_file_text.py",
        "tests": [
            "testItAddsImageExtractedTemplateToOtherVersions2",
            "testnotduplicateinsert",
            "test_returns_unchanged_when_filename_already_present",
            "test_returns_unchanged_when_filename_with_file_prefix_already_present",
            "test_returns_unchanged_when_filename_with_underscores_already_present",
            "test_no_duplicate_insert_when_already_in_other_versions",
            "test_appends_to_existing_image_extracted_with_one_arg",
            "test_appends_to_existing_image_extracted_with_two_args",
            "test_appends_to_extracted_images_template_variant",
            "test_file_prefix_stripped_when_appending_to_image_extracted",
            "test_adds_image_extracted_to_empty_other_versions_param",
            "test_appends_to_non_empty_other_versions_without_image_extracted",
            "test_creates_other_versions_param_when_information_has_none",
            "test_inserts_before_license_header_when_no_information_template",
            "test_license_header_match_is_case_insensitive",
            "test_inserts_before_category_when_no_information_and_no_license_header",
            "test_category_match_is_case_insensitive",
            "test_returns_unchanged_when_no_anchor_found",
            "test_returns_unchanged_for_empty_string",
            "test_underscores_in_filename_are_converted_to_spaces",
            "test_file_prefix_stripped_in_output",
            "test_file_prefix_and_underscores_together"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/wikitext/test_update_original_file_text.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/wikitext/test_update_template_page_file_reference.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/test_update_template_page_file_reference.py",
        "tests": [
            "test_replaces_file_reference_in_template",
            "test_replaces_all_occurrences_including_syntaxhighlight",
            "test_handles_filename_without_file_prefix",
            "test_returns_unchanged_text_when_no_match",
            "test_returns_unchanged_empty_text"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/wikitext/test_update_template_page_file_reference.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py",
        "tests": [
            "test_empty_text_returns_empty",
            "test_no_valid_lines_returns_empty",
            "test_single_valid_line",
            "test_multiple_lines_returns_latest_year",
            "test_invalid_filename_skipped",
            "test_invalid_year_format_skipped",
            "test_line_without_exclamation_skipped",
            "test_underscores_replaced_with_spaces",
            "test_filename_with_parentheses",
            "test_filename_with_hyphen",
            "test_multiple_different_years",
            "test_empty_text_returns_none",
            "test_no_template_returns_none",
            "test_template_without_gallery_world_returns_none",
            "test_valid_template_returns_last_world_file",
            "test_case_insensitive_template_name",
            "test_template_with_whitespace_in_name",
            "test_multiple_templates_uses_first",
            "test_template_with_empty_gallery_world",
            "test_template_with_gallery_but_no_content",
            "test_different_template_name_skipped",
            "test_multiple_templates_first_not_match",
            "test_template_with_no_arguments"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py",
        "tests": [
            "test_find_last_file_by_year",
            "test_single_file",
            "test_unordered_years",
            "test_underscores_replaced_with_spaces",
            "test_invalid_line_format_ignored",
            "test_invalid_year_format_ignored",
            "test_invalid_filename_format_ignored",
            "test_empty_text",
            "test_no_valid_files",
            "test_whitespace_stripped",
            "test_complex_filename",
            "test_extract_from_gallery_world",
            "test_no_owidslidersrcs_template",
            "test_no_gallery_world_argument",
            "test_empty_gallery_world",
            "test_case_insensitive_template_name",
            "test_empty_text",
            "test_single_file_in_gallery"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file2.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py",
        "tests": [
            "test_basic",
            "test_case_1",
            "test_case_2",
            "test_case_3"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/wikitext/titles_utils/last_world_file_utils/test_last_world_file_edge_cases.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/wikitext/titles_utils/test_find_main_title.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/titles_utils/test_find_main_title.py",
        "tests": [
            "test_find_main_title_svglanguages",
            "test_find_main_title_prefers_svglanguages_over_translate",
            "test_find_main_title_none_when_absent",
            "test_find_main_title_variants",
            "test_find_main_title_new",
            "test_priority_svglanguages_template",
            "test_fallback_to_url",
            "test_fallback_to_owidslidersrcs",
            "test_no_main_title_found",
            "test_empty_text",
            "test_underscores_converted_to_spaces",
            "test_whitespace_stripped"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/wikitext/titles_utils/test_find_main_title.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/wikitext/titles_utils/test_last_world_file_with_full_date.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/titles_utils/test_last_world_file_with_full_date.py",
        "tests": [
            "test_empty_text_returns_empty",
            "test_no_valid_lines_returns_empty",
            "test_single_valid_line_with_full_date",
            "test_multiple_lines_returns_latest_date",
            "test_invalid_month_skipped",
            "test_invalid_year_format_skipped",
            "test_line_without_exclamation_skipped",
            "test_underscores_replaced_with_spaces",
            "test_filename_with_parentheses",
            "test_filename_with_hyphen",
            "test_fallback_to_year_only",
            "test_mixed_date_formats",
            "test_same_year_different_month",
            "test_all_months",
            "test_whitespace_in_year_part",
            "test_invalid_filename_formats_skipped",
            "test_single_digit_day",
            "test_case_insensitive_month",
            "test_line_without_bang_skipped",
            "test_invalid_filename_regex_skipped",
            "test_invalid_month_skipped",
            "test_invalid_date_format_skipped"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/wikitext/titles_utils/test_last_world_file_with_full_date.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/wikitext/titles_utils/test_main_file.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/titles_utils/test_main_file.py",
        "tests": [
            "test_match_url_basic",
            "test_match_url_with_translation",
            "test_no_match",
            "test_match_url_with_complex_filename",
            "test_match_url_in_multiline_text",
            "test_invalid_url_domain",
            "test_url_without_file_prefix",
            "test_match_url_basic",
            "test_match_url_with_path_after_domain",
            "test_match_url_case_insensitive_domain",
            "test_match_url_with_trailing_characters",
            "test_match_url_in_wikilink",
            "test_no_match_wrong_domain",
            "test_no_match_non_svg_file",
            "test_no_match_empty_text",
            "test_match_url_with_spaces_in_filename",
            "test_match_url_encoded_filename",
            "test_invalid_url_raises_value_error",
            "test_wrong_domain_returns_none",
            "test_url_without_file_prefix_returns_none",
            "test_urlparse_value_error_returns_none",
            "test_domain_mismatch_returns_none",
            "test_extract_from_svglanguages",
            "test_extract_with_underscores_converted",
            "test_no_svglanguages_template",
            "test_case_insensitive_template_name",
            "test_empty_text",
            "test_whitespace_stripped"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/wikitext/titles_utils/test_main_file.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/utils/wikitext/titles_utils/test_match_main_title.py": {
        "action": "CREATE",
        "source": "tests/main_app/utils/wikitext/titles_utils/test_match_main_title.py",
        "tests": [
            "test_match_main_title_from_url_various",
            "test_match_main_title_from_url_new_various",
            "test_find_main_title_from_owidslidersrcs",
            "test_extract_from_gallery_world",
            "test_extract_first_file_only",
            "test_underscores_converted_to_spaces",
            "test_no_owidslidersrcs_template",
            "test_no_gallery_world_argument",
            "test_case_insensitive_template_name",
            "test_empty_text"
        ],
        "type": "unit"
    },
    "tests/main_app/utils/wikitext/titles_utils/test_match_main_title.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/integration/main_app/test_app_factory.py": {
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
        "type": "integration"
    },
    "tests/main_app/test_init.py": {
        "action": "DELETE",
        "reason": "Moved to integration tests"
    },
    "tests/unit/main_app/test_app_factory_regression_unit.py": {
        "action": "CREATE",
        "source": "tests/main_app/test_app_factory.py",
        "tests": [
            "test_format_stage_timestamp_valid",
            "test_format_stage_timestamp_empty",
            "test_format_stage_timestamp_invalid",
            "test_format_stage_timestamp_afternoon",
            "test_format_stage_timestamp_noon",
            "test_format_stage_timestamp_midnight"
        ],
        "type": "unit"
    },
    "tests/integration/main_app/test_app_factory_regression.py": {
        "action": "CREATE",
        "source": "tests/main_app/test_app_factory.py",
        "tests": [
            "test_create_app_does_not_touch_mysql_when_unconfigured",
            "test_create_app_registers_blueprints",
            "test_create_app_sets_secret_key",
            "test_create_app_configures_cookie_settings",
            "test_create_app_registers_context_processor",
            "test_create_app_registers_error_handlers",
            "test_create_app_strict_slashes_disabled",
            "test_create_app_jinja_env_configured"
        ],
        "type": "integration"
    },
    "tests/main_app/test_app_factory.py": {
        "action": "DELETE",
        "reason": "Split into unit and integration"
    },
    "tests/unit/main_app/test_config.py": {
        "action": "CREATE",
        "source": "tests/main_app/test_config.py",
        "tests": [
            "test_DbConfig",
            "test_Paths",
            "test_CookieConfig",
            "test_OAuthConfig",
            "test_Settings",
            "test_load_db_data_new",
            "test_get_paths",
            "test_env_bool",
            "test_env_int",
            "test_load_oauth_config_missing_vars",
            "test_load_oauth_config",
            "test_is_localhost",
            "test_get_settings",
            "test_get_settings_missing_secret_key",
            "test_get_settings_missing_oauth_encryption_key",
            "test_get_settings_missing_oauth_config",
            "test_load_db_data_new_empty_values",
            "test_env_bool_with_whitespace",
            "test_env_int_edge_cases",
            "test_is_localhost_partial_match",
            "test_load_oauth_config_with_defaults"
        ],
        "type": "unit"
    },
    "tests/main_app/test_config.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    },
    "tests/unit/main_app/test_data.py": {
        "action": "CREATE",
        "source": "tests/main_app/test_data.py",
        "tests": [
            "test_get_slug_categories"
        ],
        "type": "unit"
    },
    "tests/main_app/test_data.py": {
        "action": "DELETE",
        "reason": "Moved to unit tests"
    }
}
```
