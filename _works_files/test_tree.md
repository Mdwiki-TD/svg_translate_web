```
tests/
│
├── integration/
│   │
│   ├── api_services/
│   │   │
│   │   ├── clients/
│   │   │
│   │   └── files_service/
│   │       └── test_uploader_integration.py
│   │
│   ├── core/
│   │   └── test_cookie_header_client_inte.py
│   │
│   ├── database/
│   │   └── test_connection_reuse.py
│   │
│   ├── routes/
│   │   │
│   │   ├── admin/
│   │   │   │
│   │   │   ├── routes_services/
│   │   │   │
│   │   │   ├── views/
│   │   │   │   ├── test_add_lang_categories_details_template.py
│   │   │   │   ├── test_admin_jobs_routes.py
│   │   │   │   ├── test_admin_templates_routes.py
│   │   │   │   ├── test_create_owid_pages_details_template.py
│   │   │   │   ├── test_crop_main_files_details_template.py
│   │   │   │   ├── test_owid_charts_integration.py
│   │   │   │   ├── test_settings_integration.py
│   │   │   │   ├── test_templates_admin_routes_integration.py
│   │   │   │   ├── test_templates_integration.py
│   │   │   │   └── test_update_owid_charts_details_template.py
│   │   │   │
│   │   │   └── test_admin_routes.py
│   │   │
│   │   └── public/
│   │       │
│   │       ├── routes_services/
│   │       │
│   │       └── views/
│   │           ├── test_auth_routes.py
│   │           ├── test_explorer_routes_integration.py
│   │           ├── test_extract_routes_integration.py
│   │           ├── test_jobs_utils_bp_routes_integration.py
│   │           ├── test_main_route.py
│   │           ├── test_oauth_helpers_integration.py
│   │           └── test_owid_charts_routes_integration.py
│   │
│   ├── services/
│   │   │
│   │   └── auth/
│   │       └── test_auth_utils_integration.py
│   │
│   ├── utils/
│   │   │
│   │   └── wikitext/
│   │       │
│   │       └── titles_utils/
│   │
│   ├── conftest.py
│   └── test_app_factory_regression.py
│
├── js/
│   │
│   └── data_table_ajax/
│       └── macros.test.mjs
│
├── network/
│   │
│   ├── api_services/
│   │   │
│   │   ├── clients/
│   │   │   └── test_owid_client_network.py
│   │   │
│   │   └── mwclient_page/
│   │       └── test_mwclient_wraper_network.py
│   │
│   ├── __init__.py
│   └── README.md
│
├── unit/
│   │
│   ├── api_services/
│   │   │
│   │   ├── clients/
│   │   │   │
│   │   │   ├── toolforge/
│   │   │   │   ├── test_toolforge_api_service.py
│   │   │   │   ├── test_toolforge_jobs_api_service.py
│   │   │   │   ├── test_toolforge_jobs_api_service2.py
│   │   │   │   └── test_toolforge_jobs_types.py
│   │   │   │
│   │   │   ├── test_category_members_api.py
│   │   │   ├── test_commons_client.py
│   │   │   ├── test_owid_client.py
│   │   │   └── test_wikisite_client.py
│   │   │
│   │   ├── files_service/
│   │   │   ├── test_file_langs.py
│   │   │   ├── test_files_service.py
│   │   │   ├── test_files_service_objects.py
│   │   │   ├── test_upload_exceptions.py
│   │   │   └── test_uploader.py
│   │   │
│   │   ├── mwclient_page/
│   │   │   ├── test_mwclient_error.py
│   │   │   ├── test_mwclient_page.py
│   │   │   └── test_mwclient_wraper.py
│   │   │
│   │   └── test_query_api.py
│   │
│   ├── cli/
│   │
│   ├── config/
│   │   ├── test_classes.py
│   │   ├── test_flask_config.py
│   │   └── test_main_settings.py
│   │
│   ├── core/
│   │   │
│   │   ├── cookies/
│   │   │   ├── test_cookie_header_client.py
│   │   │   └── test_signing.py
│   │   │
│   │   ├── extensions/
│   │   │
│   │   ├── test_crypto.py
│   │   ├── test_extensions.py
│   │   ├── test_jinja_filters.py
│   │   └── test_rate_limit.py
│   │
│   ├── data/
│   │   └── test_data.py
│   │
│   ├── database/
│   │   │
│   │   ├── models/
│   │   │   │
│   │   │   ├── owid/
│   │   │   │   ├── test_owid_chart_record_alchemy.py
│   │   │   │   ├── test_owid_slug_redirects.py
│   │   │   │   └── test_owid_slug_redirects_model.py
│   │   │   │
│   │   │   ├── users/
│   │   │   │   ├── test_admin_users.py
│   │   │   │   ├── test_user_model.py
│   │   │   │   └── test_user_token_model.py
│   │   │   │
│   │   │   ├── test_error_log_models.py
│   │   │   ├── test_jobs_model.py
│   │   │   ├── test_template_need_update_record_alchemy.py
│   │   │   └── test_template_record_alchemy.py
│   │   │
│   │   ├── services/
│   │   │   │
│   │   │   ├── users/
│   │   │   │   ├── test_admin_service.py
│   │   │   │   ├── test_user_token_service.py
│   │   │   │   └── test_users_service.py
│   │   │   │
│   │   │   ├── utils/
│   │   │   │   ├── test_detached_instance_error.py
│   │   │   │   └── test_retry_on_disconnect.py
│   │   │   │
│   │   │   ├── test_charts_and_templates_service.py
│   │   │   ├── test_error_log_service.py
│   │   │   ├── test_jobs_service.py
│   │   │   ├── test_owid_charts_service.py
│   │   │   ├── test_owid_slug_redirects_service.py
│   │   │   ├── test_settings_service.py
│   │   │   ├── test_template_service.py
│   │   │   └── test_views_service.py
│   │   │
│   │   ├── test_exceptions.py
│   │   └── test_templates_utils.py
│   │
│   ├── decorators/
│   │   ├── test_admin_decorators.py
│   │   ├── test_admins_required.py
│   │   └── test_auth_decorators.py
│   │
│   ├── extensions/
│   │
│   ├── io/
│   │   └── test_jobs_files_service.py
│   │
│   ├── jobs/
│   │   │
│   │   ├── backends/
│   │   │   ├── test_backend_registry.py
│   │   │   ├── test_base.py
│   │   │   ├── test_thread_backend.py
│   │   │   └── test_toolforge_backend.py
│   │   │
│   │   ├── jobs_lifetime/
│   │   │   ├── test_job_creator.py
│   │   │   ├── test_jobs_canceller.py
│   │   │   ├── test_jobs_starter.py
│   │   │   └── test_reconcile.py
│   │   │
│   │   ├── test_cli_jobs.py
│   │   ├── test_job_executor.py
│   │   ├── test_job_user.py
│   │   ├── test_jobs_worker1.py
│   │   ├── test_jobs_worker_logic.py
│   │   └── test_registry.py
│   │
│   ├── jobs_workers/
│   │   │
│   │   ├── admin_jobs_workers/
│   │   │   │
│   │   │   ├── add_lang_categories_to_owid_pages/
│   │   │   │   ├── test_utils.py
│   │   │   │   └── test_worker.py
│   │   │   │
│   │   │   ├── add_svglanguages_template/
│   │   │   │   ├── test_add_svglanguages_template_utils.py
│   │   │   │   └── test_add_svglanguages_template_worker.py
│   │   │   │
│   │   │   ├── collect_templates_data/
│   │   │   │   ├── test_collect_templates_data_runner.py
│   │   │   │   ├── test_collect_templates_data_worker.py
│   │   │   │   ├── test_collect_worker_cancellation.py
│   │   │   │   ├── test_template_data_objects.py
│   │   │   │   └── test_template_data_usage.py
│   │   │   │
│   │   │   ├── create_owid_pages/
│   │   │   │   ├── test_create_owid_pages_worker.py
│   │   │   │   └── test_owid_template_converter.py
│   │   │   │
│   │   │   ├── crop_main_files/
│   │   │   │   │
│   │   │   │   ├── steps/
│   │   │   │   │   ├── test_crop_file.py
│   │   │   │   │   ├── test_crop_main_files_utils.py
│   │   │   │   │   ├── test_crop_upload.py
│   │   │   │   │   └── test_download.py
│   │   │   │   │
│   │   │   │   ├── test_crop_main_files_objects.py
│   │   │   │   └── test_crop_main_files_worker.py
│   │   │   │
│   │   │   ├── download_main_files/
│   │   │   │   ├── test_download_main_files_objects.py
│   │   │   │   ├── test_download_main_files_worker.py
│   │   │   │   └── test_zip_utils.py
│   │   │   │
│   │   │   ├── fix_nested_main_files/
│   │   │   │   ├── test_fix_nested_main_files_worker.py
│   │   │   │   └── test_fix_worker_cancellation.py
│   │   │   │
│   │   │   ├── rename_owid_pages/
│   │   │   │   ├── test_rename_owid_pages_objects.py
│   │   │   │   └── test_rename_owid_pages_worker.py
│   │   │   │
│   │   │   ├── update_owid_charts/
│   │   │   │   └── test_update_owid_charts_worker.py
│   │   │   │
│   │   │   ├── update_wikitext/
│   │   │   │
│   │   │   ├── utils/
│   │   │   │   └── test_jobs_workers_utils.py
│   │   │   │
│   │   │   └── test_slugs_helpers.py
│   │   │
│   │   ├── base_worker/
│   │   │   ├── test_base_worker.py
│   │   │   ├── test_base_worker_object.py
│   │   │   └── test_job_lifecycle_updates.py
│   │   │
│   │   ├── public_jobs_workers/
│   │   │   │
│   │   │   ├── copy_svg_langs/
│   │   │   │   │
│   │   │   │   ├── steps/
│   │   │   │   │   ├── test_extract_text.py
│   │   │   │   │   └── test_extract_titles.py
│   │   │   │   │
│   │   │   │   ├── test_copy_svg_langs_objects.py
│   │   │   │   ├── test_copy_svg_langs_worker.py
│   │   │   │   └── test_files_worker.py
│   │   │   │
│   │   │   ├── extract_files_translations/
│   │   │   │
│   │   │   └── fix_nested_jobs/
│   │   │       └── test_fix_nested_jobs_worker.py
│   │   │
│   │   ├── utils/
│   │   │   └── test_utils_init.py
│   │   │
│   │   ├── test_jobs_worker.py
│   │   ├── test_shared_objects.py
│   │   ├── test_workers_list.py
│   │   └── test_workers_utils.py
│   │
│   ├── parsers/
│   │   │
│   │   ├── wtp_mapping/
│   │   │   │
│   │   │   ├── data/
│   │   │   │   └── source-1.wiki
│   │   │   │
│   │   │   ├── test_wtp_refs.py
│   │   │   ├── test_wtp_refs_temps.py
│   │   │   └── test_wtp_temps.py
│   │   │
│   │   ├── test_template_editor.py
│   │   └── test_template_editor_delete.py
│   │
│   ├── routes/
│   │   │
│   │   ├── admin/
│   │   │   │
│   │   │   ├── views/
│   │   │   │   ├── test_admins.py
│   │   │   │   ├── test_admins_exception_handling.py
│   │   │   │   ├── test_error_logs.py
│   │   │   │   ├── test_errors_route.py
│   │   │   │   ├── test_owid_charts.py
│   │   │   │   ├── test_settings.py
│   │   │   │   ├── test_slug_redirects.py
│   │   │   │   ├── test_templates.py
│   │   │   │   └── test_users_routes.py
│   │   │   │
│   │   │   └── test_admin_sidebar.py
│   │   │
│   │   └── public/
│   │       │
│   │       ├── auth/
│   │       │
│   │       ├── routes_services/
│   │       │   ├── test_compare.py
│   │       │   ├── test_explorer_utils.py
│   │       │   └── test_thumbnail_utils.py
│   │       │
│   │       ├── views/
│   │       │   ├── test_api_routes.py
│   │       │   ├── test_jobs_utils_bp.py
│   │       │   ├── test_profile_view.py
│   │       │   ├── test_public_jobs.py
│   │       │   └── test_translate_routes.py
│   │       │
│   │       ├── test_routes_utils.py
│   │       └── test_shared_jobs_routes.py
│   │
│   ├── services/
│   │   │
│   │   ├── auth/
│   │   │   ├── test_auth_service.py
│   │   │   ├── test_current_user.py
│   │   │   ├── test_current_user_resolver.py
│   │   │   ├── test_flow.py
│   │   │   └── test_token_manager.py
│   │   │
│   │   ├── copysvg_wrapper/
│   │   │   ├── test_extract_translations.py
│   │   │   ├── test_inject_one_file.py
│   │   │   └── test_nested_fixer.py
│   │   │
│   │   ├── data/
│   │   │
│   │   ├── fix_nested/
│   │   │
│   │   ├── su_services/
│   │   │
│   │   └── utils/
│   │       └── test_decode_bytes.py
│   │
│   ├── templates_markups/
│   │   │
│   │   ├── navbar/
│   │   │
│   │   ├── sidebar/
│   │   │
│   │   └── test_sidebar.py
│   │
│   ├── utils/
│   │   │
│   │   ├── new_wikitext/
│   │   │   │
│   │   │   ├── categories/
│   │   │   │   ├── test_capitalize_category.py
│   │   │   │   ├── test_categories_utils.py
│   │   │   │   ├── test_categories_utils2.py
│   │   │   │   ├── test_extract_categories.py
│   │   │   │   ├── test_find_missing_categories.py
│   │   │   │   └── test_merge_categories.py
│   │   │   │
│   │   │   ├── main_title_finder/
│   │   │   │   ├── test_main_file.py
│   │   │   │   ├── test_main_title_finder.py
│   │   │   │   └── test_match_main_title.py
│   │   │   │
│   │   │   ├── other_versions/
│   │   │   │   ├── test_other_versions.py
│   │   │   │   ├── test_other_versions_svg_lang.py
│   │   │   │   └── test_other_versions_updater.py
│   │   │   │
│   │   │   ├── owid_gallery/
│   │   │   │   ├── test_find_newest_year.py
│   │   │   │   ├── test_owid_gallery.py
│   │   │   │   ├── test_owid_gallery_edge_cases.py
│   │   │   │   ├── test_owid_gallery_utils.py
│   │   │   │   └── test_owidslidersrcs_utils.py
│   │   │   │
│   │   │   ├── test_categories.py
│   │   │   ├── test_file_references.py
│   │   │   ├── test_file_text.py
│   │   │   ├── test_file_text_more.py
│   │   │   ├── test_insertion.py
│   │   │   ├── test_owid_source.py
│   │   │   └── test_svg_files.py
│   │   │
│   │   ├── test_categories_data.py
│   │   └── test_verify.py
│   │
│   ├── conftest.py
│   ├── test_app_factory.py
│   ├── test_app_factory_regression_unit.py
│   └── test_logging_setup.py
│
├── __init__.py
├── AUDIT_REPORT_2025-01-20.md
├── conftest.py
├── README.md
└── test_app.py

```
