# Schema ↔ Model Sync Report

**Generated:** 2026-11-15  
**Source:** `schema/backup.sql` (Adminer 5.3.0 MySQL 8.0.42 dump)  
**Models:** `www/python/src/main_app/database/models/`

---

## Summary

| Metric | Count |
|--------|-------|
| Tables checked | 13 |
| Fixes applied | 14 |
| Items needing human decision | 3 |
| Views (not modeled) | 2 |

---

## Fixes Applied

### 1. `jobs` table

| # | Severity | Column/Object | DB says | Model said | Fix applied |
|---|----------|----------------|---------|------------|-------------|
| 1 | Mismatch | `username` | `varchar(255) DEFAULT NULL` (nullable) | `nullable=False` | Changed to `Mapped[str \| None]`, `nullable=True` |
| 2 | Missing | Index `idx_status_created` | `(status, created_at)` | Not present | Added `Index("idx_status_created", "status", "created_at")` |
| 3 | Extra | Index `username` | Not present | `Index("username", "username")` | Removed |

**File:** `www/python/src/main_app/database/models/jobs.py`

---

### 2. `owid_charts` table

| # | Severity | Column/Object | DB says | Model said | Fix applied |
|---|----------|----------------|---------|------------|-------------|
| 4 | Missing | Index `idx_slug` | `(slug)` | Commented out | Added `Index("idx_slug", "slug")` |
| 5 | Missing | Index `idx_published` | `(is_published)` | Commented out | Added `Index("idx_published", "is_published")` |
| 6 | Mismatch | Unique `slug` | Name: `unique_slug` | Naming convention → `uq_owid_charts_slug` | Added explicit `UniqueConstraint("slug", name="unique_slug")` |

**File:** `www/python/src/main_app/database/models/owid_charts.py`

---

### 3. `owid_slug_redirects` table

| # | Severity | Column/Object | DB says | Model said | Fix applied |
|---|----------|----------------|---------|------------|-------------|
| 7 | Mismatch | `should_be_replaced` | `tinyint(1) DEFAULT '0'` (nullable) | `nullable=False` | Changed to `Mapped[bool \| None]`, `nullable=True` |
| 8 | Mismatch | Unique constraint | `UNIQUE KEY slug (slug)` — single column | `UniqueConstraint("slug", "redirect_to", ...)` | Changed to `UniqueConstraint("slug", name="slug")` |
| 9 | Extra | Index `idx_slug` | Not present | In model | Removed |
| 10 | Extra | Index `idx_redirect_to` | Not present | In model | Removed |

**File:** `www/python/src/main_app/database/models/owid_slug_redirects.py`

---

### 4. `settings` table

| # | Severity | Column/Object | DB says | Model said | Fix applied |
|---|----------|----------------|---------|------------|-------------|
| 11 | Mismatch | `value_type` enum | `enum('boolean','string','integer','json')` | `ValueType` has only 3 values | Added `json = "json"` to `ValueType` enum |

**File:** `www/python/src/main_app/database/models/settings.py`

---

### 5. `templates` table

| # | Severity | Column/Object | DB says | Model said | Fix applied |
|---|----------|----------------|---------|------------|-------------|
| 12 | Mismatch | Unique `title` | Name: `title` | Naming convention → `uq_templates_title` | Added explicit `UniqueConstraint("title", name="title")` |
| 13 | Missing | 5 indexes | `title_index`, `main_file`, `last_world_file`, `source`, `last_world_year` | Not present | Added all 5 indexes |

**File:** `www/python/src/main_app/database/models/templates.py`

---

### 6. `user_tokens` table

| # | Severity | Column/Object | DB says | Model said | Fix applied |
|---|----------|----------------|---------|------------|-------------|
| 14 | Mismatch | `last_used_at` | `datetime DEFAULT NULL` | `server_default=func.current_timestamp()` | Removed `server_default`, kept `nullable=True` |

**File:** `www/python/src/main_app/database/models/users.py`

---

## Items Needing Human Decision

### 15. `admin_users.username` — Foreign Key mismatch

| Aspect | Detail |
|--------|--------|
| **DB says** | No foreign key constraint on `username` |
| **Model says** | `ForeignKey("users.username", ondelete="CASCADE", onupdate="CASCADE")` |
| **Question** | Should the FK be removed from the model to match the DB, or is the FK intentional and the DB constraint was dropped? |

**File:** `www/python/src/main_app/database/models/users.py` → `AdminUserRecord`

---

### 16. `contry_job_type` — Table exists in DB, no model

| Aspect | Detail |
|--------|--------|
| **DB says** | Table exists with columns: `id`, `title`, `ar`, `contry`, `job`, `type`, `for`, `typeen`, `cat2`, `catcat` |
| **Model says** | No corresponding model found |
| **Question** | Is this table still used? Should a model be created, or is it legacy/unused? |

---

### 17. `wikilinks` — Table exists in DB, no model

| Aspect | Detail |
|--------|--------|
| **DB says** | Table exists with columns: `id`, `ar`, `en` |
| **Model says** | No corresponding model found |
| **Question** | Is this table still used? Should a model be created, or is it legacy/unused? |

---

## Tables Not Modeled (Intentional)

| Table | Reason |
|-------|--------|
| `alembic_version` | Alembic internal migration tracking |
| `owid_charts_templates` | MySQL VIEW (not a real table) |
| `templates_need_update` | MySQL VIEW (not a real table) |

---

## Informational Notes

| Table | Note |
|-------|------|
| `error_logs` | Index names in DB (`ix_error_logs_created_at`, `ix_error_logs_request_id`) match naming convention. Model uses `index=True` which auto-generates correct names. |
| `users` | No mismatches found. Model matches DB schema. |
| All tables | Collation `utf8mb4_unicode_ci` and engine `InnoDB` are consistent. |

---

## Verification

After applying fixes, run:

```bash
# Run test suite
pytest

# Optional: verify with Alembic (do not commit)
alembic revision --autogenerate -m "verify sync"
# If diff is empty, models are in sync
```

---

## Files Modified

1. `www/python/src/main_app/database/models/jobs.py`
2. `www/python/src/main_app/database/models/owid_charts.py`
3. `www/python/src/main_app/database/models/owid_slug_redirects.py`
4. `www/python/src/main_app/database/models/settings.py`
5. `www/python/src/main_app/database/models/templates.py`
6. `www/python/src/main_app/database/models/users.py`
