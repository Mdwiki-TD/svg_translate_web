```
tests/
├── integration/
│   ├── api_services/
│   │   ├── clients/
│   │   ├── utils/
│   │   └── test_upload_bot.py
│   ├── app_routes/
│   │   ├── admin/
│   │   │   ├── admin_routes/
│   │   │   │   ├── test_admin_jobs_routes.py
│   │   │   │   ├── test_owid_charts.py
│   │   │   │   ├── test_settings.py
│   │   │   │   ├── test_templates.py
│   │   │   │   └── test_templates_admin_routes.py
│   │   │   └── test_admin_routes.py
│   │   ├── admin_routes/
│   │   ├── auth/
│   │   │   ├── test_auth_routes.py
│   │   │   ├── test_auth_utils.py
│   │   │   └── test_oauth_helpers_integration.py
│   │   ├── explorer/
│   │   ├── extract/
│   │   ├── fix_nested/
│   │   ├── main/
│   │   ├── main_routes/
│   │   │   ├── test_admin_templates_routes.py
│   │   │   ├── test_explorer_routes.py
│   │   │   ├── test_extract_routes.py
│   │   │   ├── test_main_routes.py
│   │   │   └── test_owid_charts_routes.py
│   │   ├── templates/
│   │   ├── utils/
│   │   └── test_public_jobs.py
│   ├── core/
│   │   └── test_cookie_header_client.py
│   ├── data/
│   ├── db/
│   │   └── test_connection_reuse.py
│   ├── jobs_workers/
│   │   ├── add_svglanguages_template/
│   │   ├── create_owid_pages/
│   │   ├── crop_main_files/
│   │   └── utils/
│   ├── public_jobs/workers/
│   │   └── copy_svg_langs/
│   │       └── steps/
│   ├── services/
│   ├── utils/
│   │   └── wikitext/
│   │       └── titles_utils/
│   └── test_app_factory_regression.py
├── unit/
│   ├── api_services/
│   │   ├── clients/
│   │   │   ├── test_commons_client.py
│   │   │   └── test_wiki_client.py
│   │   ├── utils/
│   │   │   └── test_download_file_utils.py
│   │   ├── test_category.py
│   │   ├── test_mwclient_page.py
│   │   ├── test_mwclient_page2.py
│   │   ├── test_pages_api.py
│   │   ├── test_text_api.py
│   │   └── test_upload_bot_unit.py
│   ├── app_routes/
│   │   ├── admin/
│   │   │   ├── admin_routes/
│   │   │   │   └── test_coordinators_exception_handling.py
│   │   │   ├── test_admins_required.py
│   │   │   └── test_sidebar.py
│   │   ├── admin_routes/
│   │   ├── api/
│   │   ├── auth/
│   │   │   ├── test_auth_cookie.py
│   │   │   ├── test_auth_oauth_helpers_unit.py
│   │   │   ├── test_cookie.py
│   │   │   ├── test_oauth.py
│   │   │   └── test_rate_limit.py
│   │   ├── explorer/
│   │   ├── extract/
│   │   ├── main/
│   │   ├── main_routes/
│   │   ├── templates/
│   │   └── utils/
│   │       ├── test_compare.py
│   │       ├── test_explorer_utils.py
│   │       ├── test_get_job_detail_url.py
│   │       ├── test_routes_utils_unit.py
│   │       └── test_thumbnail_utils.py
│   ├── config/
│   │   ├── test_classes.py
│   │   └── test_main_settings.py
│   ├── core/
│   │   ├── test_cookies.py
│   │   ├── test_crypto.py
│   │   └── test_jinja_filters.py
│   ├── data/
│   ├── jobs_workers/
│   │   ├── add_svglanguages_template/
│   │   │   ├── test_add_svglanguages_template_utils.py
│   │   │   └── test_add_svglanguages_template_worker.py
│   │   ├── collect_templates_data/
│   │   │   └── test_collect_templates_data_worker.py
│   │   ├── create_owid_pages/
│   │   │   ├── test_create_owid_pages_worker.py
│   │   │   └── test_owid_template_converter.py
│   │   ├── crop_main_files/
│   │   │   ├── test_crop_file.py
│   │   │   ├── test_crop_main_files_utils.py
│   │   │   ├── test_crop_main_files_worker.py
│   │   │   ├── test_crop_main_files_worker_2.py
│   │   │   ├── test_crop_main_files_worker_run.py
│   │   │   ├── test_crop_upload.py
│   │   │   └── test_download.py
│   │   ├── download_main_files/
│   │   │   └── test_download_main_files_worker.py
│   │   ├── fix_nested_main_files/
│   │   │   └── test_fix_nested_main_files_worker.py
│   │   ├── rename_owid_pages/
│   │   │   └── test_rename_owid_pages_worker.py
│   │   ├── update_owid_charts/
│   │   │   └── test_update_owid_charts_worker.py
│   │   ├── utils/
│   │   │   └── test_jobs_workers_utils.py
│   │   ├── test_base_worker.py
│   │   ├── test_jobs_files_service.py
│   │   ├── test_jobs_worker.py
│   │   └── test_worker_cancellation.py
│   ├── public_jobs/workers/
│   │   ├── copy_svg_langs/
│   │   │   ├── steps/
│   │   │   │   ├── test_copy_svg_langs_download.py
│   │   │   │   ├── test_extract_text.py
│   │   │   │   ├── test_extract_titles.py
│   │   │   │   ├── test_extract_translations.py
│   │   │   │   ├── test_fix_nested.py
│   │   │   │   ├── test_inject.py
│   │   │   │   └── test_upload.py
│   │   │   └── test_copy_svg_langs_worker.py
│   │   └── fix_nested_jobs/
│   │       ├── test_fix_nested_jobs_processor.py
│   │       ├── test_fix_nested_jobs_processor2.py
│   │       └── test_fix_nested_jobs_worker.py
│   ├── services/
│   │   ├── test_admin_service.py
│   │   ├── test_jobs_service.py
│   │   ├── test_owid_charts_service.py
│   │   ├── test_settings_service.py
│   │   ├── test_template_service.py
│   │   ├── test_user_token_service.py
│   │   └── test_users_service_unit.py
│   ├── sqlalchemy_db/
│   │   ├── models/
│   │   │   ├── test_coordinator_record_alchemy.py
│   │   │   ├── test_owid_chart_record_alchemy.py
│   │   │   ├── test_template_need_update_record_alchemy.py
│   │   │   └── test_template_record_alchemy.py
│   │   └── test_decode_bytes.py
│   ├── utils/
│   │   ├── categories_utils/
│   │   │   ├── test_capitalize_category.py
│   │   │   ├── test_categories_utils.py
│   │   │   ├── test_extract_categories.py
│   │   │   ├── test_find_missing_categories.py
│   │   │   └── test_merge_categories.py
│   │   ├── wikitext/
│   │   │   ├── temps_bot/
│   │   │   │   ├── test_get_files_list.py
│   │   │   │   ├── test_get_titles.py
│   │   │   │   └── test_temps_bot.py
│   │   │   ├── titles_utils/
│   │   │   │   ├── last_world_file_utils/
│   │   │   │   │   ├── test_last_world_file.py
│   │   │   │   │   ├── test_last_world_file2.py
│   │   │   │   │   └── test_last_world_file_edge_cases.py
│   │   │   │   ├── test_find_main_title.py
│   │   │   │   ├── test_last_world_file_with_full_date.py
│   │   │   │   ├── test_main_file.py
│   │   │   │   └── test_match_main_title.py
│   │   │   ├── test_appendImageExtractedTemplate.py
│   │   │   ├── test_before_methods.py
│   │   │   ├── test_files_text.py
│   │   │   ├── test_other_versions.py
│   │   │   ├── test_temp_source.py
│   │   │   ├── test_template_page.py
│   │   │   ├── test_text_utils.py
│   │   │   ├── test_update_original_file_text.py
│   │   │   └── test_update_template_page_file_reference.py
│   │   └── test_verify.py
│   ├── test_app_factory_regression_unit.py
│   ├── test_data.py
│   └── test_init.py
├── conftest.py
├── prompt_test_classification_agent.md
├── test_app.py
└── test_logger_config.py

```
