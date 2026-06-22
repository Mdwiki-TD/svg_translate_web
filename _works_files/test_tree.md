```
tests/
├── integration/
│   ├── api_services/
│   │   ├── clients/
│   │   ├── files_service/
│   │   │   └── test_upload_bot_integration.py
│   │   └── utils/
│   ├── app_routes/
│   │   ├── admin/
│   │   │   ├── admin_routes/
│   │   │   │   ├── test_admin_jobs_routes.py
│   │   │   │   ├── test_create_owid_pages_details_template.py
│   │   │   │   ├── test_owid_charts.py
│   │   │   │   ├── test_settings_integration.py
│   │   │   │   ├── test_templates.py
│   │   │   │   ├── test_templates_admin_routes.py
│   │   │   │   └── test_update_owid_charts_details_template.py
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
│   │   ├── test_jobs_utils_bp_routes.py
│   │   └── test_public_jobs_integration.py
│   ├── core/
│   │   └── test_cookie_header_client_inte.py
│   ├── db/
│   │   └── test_connection_reuse.py
│   ├── jobs_workers/
│   │   ├── add_svglanguages_template/
│   │   ├── create_owid_pages/
│   │   ├── crop_main_files/
│   │   └── utils/
│   ├── public_jobs_workers/
│   │   └── copy_svg_langs/
│   │       └── steps/
│   ├── services/
│   ├── utils/
│   │   └── wikitext/
│   │       └── titles_utils/
│   └── test_app_factory_regression.py
├── network/
│   ├── api_services/
│   │   ├── mwclient_page/
│   │   │   └── test_mwclient_wraper_network.py
│   │   └── test_query_api_network.py
│   ├── __init__.py
│   ├── network_conftest.py
│   └── README.md
├── unit/
│   ├── admin/
│   │   ├── routes/
│   │   │   ├── test_coordinators.py
│   │   │   ├── test_coordinators_exception_handling.py
│   │   │   ├── test_settings.py
│   │   │   ├── test_slug_redirects.py
│   │   │   └── test_users_routes.py
│   │   ├── test_admins_required.py
│   │   └── test_sidebar.py
│   ├── api_services/
│   │   ├── clients/
│   │   │   ├── test_commons_client.py
│   │   │   ├── test_owid_client.py
│   │   │   └── test_wiki_client.py
│   │   ├── files_service/
│   │   │   ├── test_download_file_utils.py
│   │   │   ├── test_files_helpers.py
│   │   │   └── test_upload_bot.py
│   │   ├── mwclient_page/
│   │   │   ├── test_mwclient_error.py
│   │   │   ├── test_mwclient_page.py
│   │   │   └── test_mwclient_wraper.py
│   │   ├── utils/
│   │   ├── test_category.py
│   │   └── test_query_api.py
│   ├── app_routes/
│   │   ├── auth/
│   │   │   ├── test_rate_limit.py
│   │   │   └── test_utils.py
│   │   ├── utils/
│   │   │   ├── test_compare.py
│   │   │   ├── test_explorer_utils.py
│   │   │   ├── test_get_job_detail_url.py
│   │   │   ├── test_routes_utils.py
│   │   │   ├── test_routes_utils_unit.py
│   │   │   └── test_thumbnail_utils.py
│   │   ├── test_api_routes.py
│   │   ├── test_jobs_routes_utils.py
│   │   ├── test_profile.py
│   │   └── test_public_jobs.py
│   ├── config/
│   │   ├── test_classes.py
│   │   ├── test_flask_config.py
│   │   └── test_main_settings.py
│   ├── core/
│   │   ├── cookies/
│   │   │   ├── test_cookie.py
│   │   │   └── test_cookie_header_client.py
│   │   ├── test_crypto.py
│   │   └── test_jinja_filters.py
│   ├── data/
│   │   └── test_data.py
│   ├── db/
│   │   ├── models/
│   │   │   ├── test_coordinator_record_alchemy.py
│   │   │   ├── test_jobs_model.py
│   │   │   ├── test_jobs_modules.py
│   │   │   ├── test_owid_chart_record_alchemy.py
│   │   │   ├── test_owid_slug_redirects.py
│   │   │   ├── test_owid_slug_redirects_model.py
│   │   │   ├── test_template_need_update_record_alchemy.py
│   │   │   ├── test_template_record_alchemy.py
│   │   │   ├── test_users.py
│   │   │   └── test_views.py
│   │   ├── services/
│   │   │   ├── utils/
│   │   │   │   ├── test_db_guard_model.py
│   │   │   │   ├── test_detachedinstanceerror.py
│   │   │   │   └── test_retry_on_disconnect.py
│   │   │   ├── test_admin_service.py
│   │   │   ├── test_delete_service.py
│   │   │   ├── test_jobs_service.py
│   │   │   ├── test_owid_charts_service.py
│   │   │   ├── test_owid_slug_redirects_service.py
│   │   │   ├── test_settings_service.py
│   │   │   ├── test_template_service.py
│   │   │   ├── test_user_token_service.py
│   │   │   ├── test_users_service.py
│   │   │   └── test_views_service.py
│   │   ├── test_db_init.py
│   │   ├── test_exceptions.py
│   │   └── test_templates_utils.py
│   ├── jobs_workers/
│   │   ├── admin_jobs_workers/
│   │   │   ├── add_svglanguages_template/
│   │   │   │   ├── test_add_svglanguages_template_utils.py
│   │   │   │   └── test_add_svglanguages_template_worker.py
│   │   │   ├── admin_jobs_workers/
│   │   │   │   ├── add_svglanguages_template/
│   │   │   │   ├── collect_templates_data/
│   │   │   │   ├── create_owid_pages/
│   │   │   │   ├── crop_main_files/
│   │   │   │   ├── download_main_files/
│   │   │   │   ├── fix_nested_main_files/
│   │   │   │   ├── rename_owid_pages/
│   │   │   │   └── update_owid_charts/
│   │   │   ├── collect_templates_data/
│   │   │   │   └── test_collect_templates_data_worker.py
│   │   │   ├── create_owid_pages/
│   │   │   │   ├── test_create_owid_pages_worker.py
│   │   │   │   └── test_owid_template_converter.py
│   │   │   ├── crop_main_files/
│   │   │   │   ├── test_crop_file.py
│   │   │   │   ├── test_crop_main_files_objects.py
│   │   │   │   ├── test_crop_main_files_utils.py
│   │   │   │   ├── test_crop_main_files_worker.py
│   │   │   │   ├── test_crop_main_files_worker_run.py
│   │   │   │   ├── test_crop_upload.py
│   │   │   │   ├── test_crop_utils.py
│   │   │   │   └── test_download.py
│   │   │   ├── download_main_files/
│   │   │   │   ├── test_download_helper.py
│   │   │   │   ├── test_download_main_files_objects.py
│   │   │   │   └── test_download_main_files_worker.py
│   │   │   ├── fix_nested_main_files/
│   │   │   │   └── test_fix_nested_main_files_worker.py
│   │   │   ├── public_jobs_workers/
│   │   │   │   ├── copy_svg_langs/
│   │   │   │   │   └── steps/
│   │   │   │   └── fix_nested_jobs/
│   │   │   ├── rename_owid_pages/
│   │   │   │   └── test_rename_owid_pages_worker.py
│   │   │   ├── update_owid_charts/
│   │   │   │   └── test_update_owid_charts_worker.py
│   │   │   ├── utils/
│   │   │   │   └── test_jobs_workers_utils.py
│   │   │   ├── test_jobs_files_service.py
│   │   │   ├── test_jobs_worker.py
│   │   │   ├── test_slugs_helpers.py
│   │   │   ├── test_worker_cancellation.py
│   │   │   └── test_workers_list.py
│   │   ├── public_jobs_workers/
│   │   │   ├── copy_svg_langs/
│   │   │   │   ├── steps/
│   │   │   │   │   ├── test_extract_text.py
│   │   │   │   │   ├── test_extract_titles.py
│   │   │   │   │   ├── test_extract_translations.py
│   │   │   │   │   └── test_inject_one_file.py
│   │   │   │   ├── test_copy_svg_langs_objects.py
│   │   │   │   └── test_copy_svg_langs_worker.py
│   │   │   └── fix_nested_jobs/
│   │   │       ├── test_fix_nested_jobs_processor.py
│   │   │       ├── test_fix_nested_jobs_processor2.py
│   │   │       └── test_fix_nested_jobs_worker.py
│   │   ├── utils/
│   │   │   └── test_utils_init.py
│   │   ├── test_base_worker_object.py
│   │   ├── test_jobs_worker_logic.py
│   │   └── test_shared_objects.py
│   ├── public/
│   │   └── app_routes/
│   │       ├── auth/
│   │       └── utils/
│   ├── shared/
│   │   ├── core/
│   │   │   └── cookies/
│   │   ├── data/
│   │   ├── fix_nested/
│   │   │   └── test_fix_nested_worker.py
│   │   ├── su_services/
│   │   └── test_decode_bytes.py
│   ├── su_services/
│   │   ├── test_auth_service.py
│   │   ├── test_auth_users_service.py
│   │   ├── test_current_user.py
│   │   ├── test_jobs_files_service_new.py
│   │   └── test_mwoauth_handshake.py
│   ├── utils/
│   │   ├── wikitext/
│   │   │   ├── categories_utils/
│   │   │   │   ├── test_capitalize_category.py
│   │   │   │   ├── test_categories_utils.py
│   │   │   │   ├── test_categories_utils2.py
│   │   │   │   ├── test_extract_categories.py
│   │   │   │   ├── test_find_missing_categories.py
│   │   │   │   └── test_merge_categories.py
│   │   │   ├── owid_sliders_rcs/
│   │   │   ├── titles_utils/
│   │   │   │   ├── last_world_file_utils/
│   │   │   │   │   ├── test_last_world_file2.py
│   │   │   │   │   ├── test_last_world_file_edge_cases.py
│   │   │   │   │   └── test_last_world_file_utils.py
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
│   │   │   ├── test_temps_bot.py
│   │   │   ├── test_text_utils.py
│   │   │   ├── test_update_original_file_text.py
│   │   │   ├── test_update_template_page_file_reference.py
│   │   │   └── test_wikitext_init.py
│   │   └── test_verify.py
│   ├── test_app_factory_regression_unit.py
│   ├── test_extensions.py
│   └── test_init.py
├── __init__.py
├── conftest.py
├── test_app.py
└── test_logger_config.py

```