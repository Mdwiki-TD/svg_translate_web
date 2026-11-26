```
src/
│
├── main_app/
│   │
│   ├── api_services/
│   │   │
│   │   ├── clients/
│   │   │   │
│   │   │   ├── toolforge/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── toolforge_api_service.py
│   │   │   │   ├── toolforge_jobs_api_service.py
│   │   │   │   └── toolforge_jobs_types.py
│   │   │   │
│   │   │   ├── __init__.py
│   │   │   ├── category_members_api.py
│   │   │   ├── commons_client.py
│   │   │   ├── http_client.py
│   │   │   ├── http_client_helper.py
│   │   │   ├── objects.py
│   │   │   ├── owid_client.py
│   │   │   └── wikisite_client.py
│   │   │
│   │   ├── files_service/
│   │   │   ├── __init__.py
│   │   │   ├── exceptions.py
│   │   │   ├── objects.py
│   │   │   ├── save_file.py
│   │   │   ├── service.py
│   │   │   └── uploader.py
│   │   │
│   │   ├── mwclient_page/
│   │   │   ├── __init__.py
│   │   │   ├── mwclient_error.py
│   │   │   └── mwclient_wraper.py
│   │   │
│   │   ├── __init__.py
│   │   ├── query_api.py
│   │   └── README.md
│   │
│   ├── cli/
│   │   ├── __init__.py
│   │   └── errors_cli.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── classes.py
│   │   └── flask_config.py
│   │
│   ├── core/
│   │   │
│   │   ├── cookies/
│   │   │   ├── __init__.py
│   │   │   ├── cookie_header_client.py
│   │   │   └── signing.py
│   │   │
│   │   ├── extensions/
│   │   │   ├── __init__.py
│   │   │   └── csrf_protect.py
│   │   │
│   │   ├── __init__.py
│   │   ├── crypto.py
│   │   ├── jinja_filters.py
│   │   └── rate_limit.py
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── owid_charts.csv
│   │   ├── templates_slugs_topics.json
│   │   └── topics_categories.json
│   │
│   ├── database/
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── error_log_models.py
│   │   │   ├── jobs.py
│   │   │   ├── owid_charts.py
│   │   │   ├── owid_slug_redirects.py
│   │   │   ├── settings.py
│   │   │   ├── templates.py
│   │   │   ├── users.py
│   │   │   └── views.py
│   │   │
│   │   ├── services/
│   │   │   │
│   │   │   ├── config/
│   │   │   │   └── settings_service.py
│   │   │   │
│   │   │   ├── users/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── admin_service.py
│   │   │   │   ├── user_token_service.py
│   │   │   │   └── users_service.py
│   │   │   │
│   │   │   ├── utils/
│   │   │   │   ├── __init__.py
│   │   │   │   └── retry_on_disconnect.py
│   │   │   │
│   │   │   ├── __init__.py
│   │   │   ├── charts_and_templates_service.py
│   │   │   ├── crud_service.py
│   │   │   ├── error_log_service.py
│   │   │   ├── jobs_service.py
│   │   │   ├── owid_charts_service.py
│   │   │   ├── owid_slug_redirects_service.py
│   │   │   ├── template_service.py
│   │   │   └── views_service.py
│   │   │
│   │   ├── __init__.py
│   │   ├── create_helper.py
│   │   ├── db_base.py
│   │   ├── db_builder.py
│   │   ├── exceptions.py
│   │   └── templates_utils.py
│   │
│   ├── decorators/
│   │   ├── __init__.py
│   │   ├── admin_decorators.py
│   │   └── auth_decorators.py
│   │
│   ├── io/
│   │   ├── __init__.py
│   │   └── jobs_files_service.py
│   │
│   ├── jobs/
│   │   │
│   │   ├── backends/
│   │   │   ├── __init__.py
│   │   │   ├── backend_registry.py
│   │   │   ├── base.py
│   │   │   ├── thread_backend.py
│   │   │   ├── thread_cancel_registry.py
│   │   │   └── toolforge_backend.py
│   │   │
│   │   ├── jobs_lifetime/
│   │   │   ├── __init__.py
│   │   │   ├── job_creator.py
│   │   │   ├── jobs_canceller.py
│   │   │   ├── jobs_starter.py
│   │   │   └── reconcile.py
│   │   │
│   │   ├── __init__.py
│   │   ├── base_worker.py
│   │   ├── cli_jobs.py
│   │   ├── job_executor.py
│   │   ├── job_user.py
│   │   ├── objects.py
│   │   ├── registry.py
│   │   ├── shared_objects.py
│   │   └── utils.py
│   │
│   ├── jobs_workers/
│   │   │
│   │   ├── admin_jobs_workers/
│   │   │   │
│   │   │   ├── add_lang_categories_to_owid_pages/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   ├── utils.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── add_svglanguages_template/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   ├── utils.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── collect_templates_data/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── create_owid_pages/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   ├── owid_template_converter.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── crop_main_files/
│   │   │   │   │
│   │   │   │   ├── steps/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── crop_file.py
│   │   │   │   │   ├── download.py
│   │   │   │   │   └── upload.py
│   │   │   │   │
│   │   │   │   ├── __init__.py
│   │   │   │   ├── files_processor.py
│   │   │   │   ├── objects.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── download_main_files/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   ├── worker.py
│   │   │   │   └── zip_utils.py
│   │   │   │
│   │   │   ├── fix_nested_main_files/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── rename_owid_pages/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── update_owid_charts/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── update_wikitext/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── files_processor.py
│   │   │   │   ├── objects.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── __init__.py
│   │   │   ├── slugs_helpers.py
│   │   │   └── workers_list.py
│   │   │
│   │   ├── public_jobs_workers/
│   │   │   │
│   │   │   ├── copy_svg_langs/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── files_worker.py
│   │   │   │   ├── forms.py
│   │   │   │   ├── objects.py
│   │   │   │   ├── steps.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── extract_files_translations/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── fix_nested_jobs/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   └── worker.py
│   │   │   │
│   │   │   ├── __init__.py
│   │   │   └── workers_list_public.py
│   │   │
│   │   ├── __init__.py
│   │   └── workers_lists.py
│   │
│   ├── parsers/
│   │   │
│   │   ├── wtp_mapping/
│   │   │   ├── __init__.py
│   │   │   ├── wtp_refs.py
│   │   │   ├── wtp_refs_temps.py
│   │   │   └── wtp_temps.py
│   │   │
│   │   ├── __init__.py
│   │   └── template_editor.py
│   │
│   ├── routes/
│   │   │
│   │   ├── admin/
│   │   │   │
│   │   │   ├── routes_services/
│   │   │   │   ├── toolforge_jobs_mapping.py
│   │   │   │   └── toolforge_jobs_service.py
│   │   │   │
│   │   │   ├── views/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── admins.py
│   │   │   │   ├── error_logs.py
│   │   │   │   ├── errors_route.py
│   │   │   │   ├── owid_charts.py
│   │   │   │   ├── settings.py
│   │   │   │   ├── slug_redirects.py
│   │   │   │   ├── templates.py
│   │   │   │   ├── toolforge_jobs_view.py
│   │   │   │   └── users.py
│   │   │   │
│   │   │   ├── __init__.py
│   │   │   ├── admin_panel.py
│   │   │   ├── admin_routes_registrar.py
│   │   │   ├── admin_sidebar.py
│   │   │   ├── flask_admin_panel.py
│   │   │   └── flask_admin_panel_models.py
│   │   │
│   │   ├── public/
│   │   │   │
│   │   │   ├── routes_services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── compare.py
│   │   │   │   ├── explorer_utils.py
│   │   │   │   └── thumbnail_utils.py
│   │   │   │
│   │   │   ├── views/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── api_routes.py
│   │   │   │   ├── auth_route.py
│   │   │   │   ├── explorer_routes.py
│   │   │   │   ├── extract_routes.py
│   │   │   │   ├── inject_routes.py
│   │   │   │   ├── jobs_utils_bp.py
│   │   │   │   ├── main_route.py
│   │   │   │   ├── mapping.py
│   │   │   │   ├── owid_charts_routes.py
│   │   │   │   ├── profile_view.py
│   │   │   │   ├── templates_view.py
│   │   │   │   └── translate_routes.py
│   │   │   │
│   │   │   ├── __init__.py
│   │   │   ├── public_routes_registrar.py
│   │   │   ├── routes_utils.py
│   │   │   ├── shared_jobs_registrar.py
│   │   │   └── shared_jobs_routes.py
│   │   │
│   │   ├── __init__.py
│   │   ├── error_pages.py
│   │   ├── objects.py
│   │   └── routes_factory.py
│   │
│   ├── services/
│   │   │
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── auth_exceptions.py
│   │   │   ├── auth_service.py
│   │   │   ├── current_user.py
│   │   │   ├── current_user_resolver.py
│   │   │   ├── flow.py
│   │   │   ├── mapping.py
│   │   │   └── token_manager.py
│   │   │
│   │   ├── copysvg_wrapper/
│   │   │   ├── __init__.py
│   │   │   ├── extract_translations.py
│   │   │   ├── inject_one_file.py
│   │   │   ├── mapping.py
│   │   │   └── nested_fixer.py
│   │   │
│   │   ├── fix_nested/
│   │   │   ├── __init__.py
│   │   │   └── objects.py
│   │   │
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   └── decode_bytes.py
│   │   │
│   │   ├── __init__.py
│   │   └── owid_charts_utils.py
│   │
│   ├── templates_markups/
│   │   │
│   │   ├── navbar/
│   │   │   ├── __init__.py
│   │   │   ├── mapping.py
│   │   │   ├── nav_bar.py
│   │   │   └── navbar_list.py
│   │   │
│   │   ├── sidebar/
│   │   │   ├── __init__.py
│   │   │   ├── mapping.py
│   │   │   └── sidebar.py
│   │   │
│   │   └── __init__.py
│   │
│   ├── utils/
│   │   │
│   │   ├── new_wikitext/
│   │   │   ├── __init__.py
│   │   │   ├── categories.py
│   │   │   ├── file_references.py
│   │   │   ├── file_text.py
│   │   │   ├── insertion.py
│   │   │   ├── main_title_finder.py
│   │   │   ├── other_versions.py
│   │   │   ├── owid_gallery.py
│   │   │   ├── owid_source.py
│   │   │   └── svg_files.py
│   │   │
│   │   ├── __init__.py
│   │   ├── categories_data.py
│   │   └── verify.py
│   │
│   ├── __init__.py
│   ├── app_factory.py
│   └── README.md
│
├── offline/
│   ├── error.txt
│   └── sitemap.py
│
├── static/
│   │
│   ├── css/
│   │   ├── navbar.css
│   │   ├── sidebar-desktop.css
│   │   ├── sidebar-mobile.css
│   │   └── style.css
│   │
│   ├── images/
│   │
│   ├── js/
│   │   │
│   │   ├── data_table_ajax/
│   │   │   ├── macros.js
│   │   │   └── table.js
│   │   │
│   │   ├── auto-refresh.js
│   │   ├── autocomplete.js
│   │   ├── card-tools.js
│   │   ├── dark-mode.js
│   │   ├── sidebar.js
│   │   └── SVGLanguages.js
│   │
│   ├── favicon.ico
│   └── toolinfo.json
│
├── templates/
│   │
│   ├── _macros/
│   │
│   ├── admin/
│   │   │
│   │   └── bs4_admin/
│   │       │
│   │       ├── file/
│   │       │   │
│   │       │   └── modals/
│   │       │
│   │       ├── model/
│   │       │   │
│   │       │   └── modals/
│   │       │
│   │       └── rediscli/
│   │
│   ├── admins/
│   │   │
│   │   ├── owid_charts/
│   │   │
│   │   ├── slug_redirects/
│   │   │
│   │   └── tf_jobs/
│   │
│   ├── explorer/
│   │
│   ├── extract/
│   │
│   ├── inject/
│   │   └── example.json
│   │
│   ├── jobs_templates/
│   │   │
│   │   ├── _ajax_templates/
│   │   │
│   │   ├── _help_templates/
│   │   │
│   │   ├── admin_templates/
│   │   │   │
│   │   │   ├── add_lang_categories_to_owid_pages/
│   │   │   │
│   │   │   ├── add_svglanguages_template/
│   │   │   │
│   │   │   ├── collect_templates_data/
│   │   │   │
│   │   │   ├── create_owid_pages/
│   │   │   │
│   │   │   ├── crop_main_files/
│   │   │   │
│   │   │   ├── download_main_files/
│   │   │   │
│   │   │   ├── fix_nested_main_files/
│   │   │   │
│   │   │   ├── rename_owid_pages/
│   │   │   │
│   │   │   ├── update_owid_charts/
│   │   │   │
│   │   │   └── update_wikitext/
│   │   │
│   │   └── public/
│   │       │
│   │       ├── copy_svg_langs/
│   │       │
│   │       ├── extract_files_translations/
│   │       │
│   │       └── fix_nested_jobs/
│   │
│   ├── owid_charts/
│   │
│   └── translate/
│
├── __init__.py
├── app.py
├── bootstrap.py
├── import_owid_charts.py
├── logging_setup.py
└── uwsgi.ini

```