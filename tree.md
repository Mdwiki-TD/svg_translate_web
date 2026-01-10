```
src/
├── app/
│   ├── config.py
│   ├── crypto.py
│   ├── routes_utils.py
│   ├── template_service.py
│   ├── __init__.py
│   ├── admins/
│   │   ├── admins_required.py
│   │   ├── admin_service.py
│   │   └── __init__.py
│   ├── app_routes/
│   │   ├── __init__.py
│   │   ├── admin/
│   │   │   ├── routes.py
│   │   │   ├── sidebar.py
│   │   │   ├── __init__.py
│   │   │   └── admin_routes/
│   │   │       ├── coordinators.py
│   │   │       ├── jobs.py
│   │   │       ├── recent.py
│   │   │       ├── templates.py
│   │   │       └── __init__.py
│   │   ├── auth/
│   │   │   ├── cookie.py
│   │   │   ├── oauth.py
│   │   │   ├── rate_limit.py
│   │   │   ├── routes.py
│   │   │   └── __init__.py
│   │   ├── cancel_restart/
│   │   │   ├── routes.py
│   │   │   └── __init__.py
│   │   ├── explorer/
│   │   │   ├── compare.py
│   │   │   ├── routes.py
│   │   │   ├── thumbnail_utils.py
│   │   │   ├── utils.py
│   │   │   └── __init__.py
│   │   ├── fix_nested/
│   │   │   ├── explorer_routes.py
│   │   │   ├── fix_utils.py
│   │   │   ├── routes.py
│   │   │   └── __init__.py
│   │   ├── main/
│   │   │   ├── routes.py
│   │   │   └── __init__.py
│   │   ├── tasks/
│   │   │   ├── args_utils.py
│   │   │   ├── routes.py
│   │   │   └── __init__.py
│   │   └── templates/
│   │       ├── category.py
│   │       ├── routes.py
│   │       └── __init__.py
│   ├── cookies/
│   │   └── __init__.py
│   ├── db/
│   │   ├── db_class.py
│   │   ├── db_CoordinatorsDB.py
│   │   ├── db_CreateUpdate.py
│   │   ├── db_Jobs.py
│   │   ├── db_StageStore.py
│   │   ├── db_TasksListDB.py
│   │   ├── db_Templates.py
│   │   ├── fix_nested_task_store.py
│   │   ├── svg_db.py
│   │   ├── task_store_pymysql.py
│   │   ├── utils.py
│   │   └── __init__.py
│   ├── jobs_workers/
│   │   ├── collect_main_files_worker.py
│   │   ├── fix_nested_main_files_worker.py
│   │   ├── jobs_service.py
│   │   ├── jobs_worker.py
│   │   └── __init__.py
│   ├── tasks/
│   │   ├── tasks_utils.py
│   │   ├── __init__.py
│   │   ├── downloads/
│   │   │   ├── download.py
│   │   │   └── __init__.py
│   │   ├── extract/
│   │   │   ├── extract_task.py
│   │   │   └── __init__.py
│   │   ├── fix_nested/
│   │   │   ├── fix_nested_tasks.py
│   │   │   └── __init__.py
│   │   ├── injects/
│   │   │   ├── inject_tasks.py
│   │   │   └── __init__.py
│   │   ├── texts/
│   │   │   ├── start_bot.py
│   │   │   ├── text_bot.py
│   │   │   └── __init__.py
│   │   ├── titles/
│   │   │   ├── temps_bot.py
│   │   │   ├── titles_tasks.py
│   │   │   ├── __init__.py
│   │   │   └── utils/
│   │   │       ├── main_file.py
│   │   │       └── __init__.py
│   │   └── uploads/
│   │       ├── up.py
│   │       ├── upload_bot.py
│   │       ├── wiki_client.py
│   │       └── __init__.py
│   ├── threads/
│   │   ├── task_threads.py
│   │   ├── web_run_task.py
│   │   └── __init__.py
│   └── users/
│       ├── current.py
│       ├── store.py
│       └── __init__.py
├── static/
│   ├── js/
│   └── css/
└── templates/
    └── index.html
```
