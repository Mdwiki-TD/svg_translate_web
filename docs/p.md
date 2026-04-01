```
src/
├── __init__.py
├── app.py
├── main_app/
│   ├── app_routes/
│   │   ├── copy_svg_langs/
│   │   │   ├── __init__.py
│   │   │   ├── db/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── copy_svg_langs_store.py
│   │   │   │   ├── db_CreateUpdate.py
│   │   │   │   └── db_StageStore.py
│   │   │   ├── routes.py
│   │   │   └── worker.py
│   │   ├── fix_nested/
│   │   │   ├── __init__.py
│   │   │   ├── fix_nested_store.py
│   │   │   ├── routes.py
│   │   │   └── worker.py
```

or

```
src/
├── __init__.py
├── app.py
├── main_app/
│   ├── app_routes/
│   │   ├── copy_svg_langs/
│   │   │   ├── __init__.py
│   │   │   └── routes.py
│   │   └── fix_nested/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── worker.py
│   └── db/
│   │   ├── __init__.py
│   │   ├── copy_svg_langs_store/
│   │   │   ├── __init__.py
│   │   │   ├── db_CreateUpdate.py
│   │   │   └── db_StageStore.py
│   │   └── fix_nested_store.py
│   ├── workers/
│       ├── copy_svg_langs_worker.py
│       └── fix_nested_worker.py
```
