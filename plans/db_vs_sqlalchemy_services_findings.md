# Findings: `db/services` vs `sqlalchemy_db/services` — NOT Functionally Equivalent

Detailed side-by-side analysis of every function in all six service modules.
Each finding includes the exact code difference and its observable impact.

---

## `jobs_service.py`

### 🔴 BUG 1 — `update_job_status(status="running")` raises `TypeError` at runtime

**Old** (`db/services`):
```python
def update_running_status(job_id: int, job_type: str, result_file: str | None = None) -> JobRecord:
    ...

def update_job_status(job_id, status, result_file=None, *, job_type):
    if status == "running":
        return update_running_status(job_id, job_type, result_file)  # positional OK
```

**New** (`sqlalchemy_db/services`):
```python
def update_running_status(job_id: int, result_file: str | None = None, *, job_type: str) -> JobRecord:
    #                                   ^^^^^^^^^^^^ signature changed — job_type is now keyword-only

def update_job_status(job_id, status, result_file=None, *, job_type):
    if status == "running":
        return update_running_status(job_id, result_file, job_type)  # 🔴 passes job_type positionally → TypeError
```

**Impact**: Every background job crashes on start. `base_worker.py:151` calls
`jobs_service.update_job_status(job_id, "running", ...)` — this is the first thing every worker does.

**Fix**: Change to `update_running_status(job_id, result_file, job_type=job_type)`.

---

### 🔴 BUG 2 — `list_jobs(job_type=...)` filter is silently discarded

**Old**: delegates to `store.list(job_type=job_type)` which builds `WHERE job_type = %s`.

**New**:
```python
query = session.query(JobRecord)
if job_type:
    query.filter(JobRecord.job_type == job_type)   # 🔴 result not reassigned — filter is lost
return query.order_by(JobRecord.created_at.desc()).limit(limit).all()
```

**Impact**: The admin jobs page and public jobs page always return all job types regardless
of the `job_type` parameter. Filtering appears to work but does nothing.

**Fix**: `query = query.filter(JobRecord.job_type == job_type)`.

---

### 🟡 DIFFERENCE 3 — `cancel_job` no longer guards on current status

**Old** SQL: `UPDATE jobs SET status='cancelled' WHERE id=%s AND status IN ('pending','running')`
— only cancels jobs that haven't finished yet.

**New**:
```python
job = session.query(JobRecord).filter(JobRecord.id == job_id, JobRecord.job_type == job_type).first()
if job:
    job.status = "cancelled"   # 🟡 no status guard — overwrites completed/failed jobs too
    job.completed_at = datetime.now(UTC)
    ...
    return True
return False
```

**Impact**: A completed or failed job can be retroactively marked as cancelled, corrupting
audit history. Return value also changes: old returns `False` when job exists but is not
cancellable; new returns `True` for any existing job.

---

### 🟡 DIFFERENCE 4 — `list_charts` now hard-caps at 100 rows

**Old**: `store.list()` — no LIMIT, returns all rows from the join view.

**New**: `session.query(OwidChartRecord).limit(limit).all()` with default `limit=100`.

**Impact**: If there are more than 100 charts, the API endpoint `/api/owid-charts` returns
incomplete data, and the `summary` totals are computed from the truncated list — they will
be wrong.

---

## `settings_service.py`

### 🔴 BUG 5 — `create_setting` returns the ORM object instead of `bool`, skips duplicate check

**Old**:
```python
def create_setting(key, title, value_type) -> bool:
    value = default_value_types.get(value_type, "")
    store = get_settings_db()
    return store.create(key, title, value_type, value)  # returns bool, False if key exists
```

**New**:
```python
def create_setting(key, title, value_type) -> bool:   # return type annotation is wrong
    ...
    job = SettingRecord(key=key, title=title, value=value, value_type=value_type)
    session.add(job)
    session.commit()   # 🔴 raises IntegrityError on duplicate key instead of returning False
    session.refresh(job)
    return job         # 🔴 returns SettingRecord, not bool
```

**Impact**: The caller in `admin_routes/settings.py` does `if success:` — a `SettingRecord`
is always truthy, so the success branch always runs even when the insert failed (or
raised an exception). Duplicate key creates an unhandled 500 error.

---

### 🔴 BUG 6 — `update_setting` loses type-aware serialization

**Old** uses `_serialize_value(value, value_type)`:
- `boolean` → `"true"` / `"false"` (lowercase)
- `integer` → `str(int(value))`
- `json` → `json.dumps(value, ensure_ascii=False)`
- Falls back to `str(value)` for `string`

**New**:
```python
setting.value = str(value)   # 🔴 always raw str() — no type awareness
```

**Impact**:
| value_type | value passed | old stores | new stores |
|---|---|---|---|
| boolean | `True` | `"true"` | `"True"` (wrong case) |
| boolean | `False` | `"false"` | `"False"` (wrong case) |
| json | `{"a": 1}` | `'{"a": 1}'` | `"{'a': 1}"` (Python repr, invalid JSON) |
| integer | `42` | `"42"` | `"42"` ✓ |
| string | `"hello"` | `"hello"` ✓ | `"hello"` ✓ |

Boolean settings read back through `_parse_setting_value` expect `"on"` for truthy and
anything else for falsy — so the wrong-case `"True"` string would be treated as falsy.

---

### 🔴 BUG 7 — `update_setting` upserts instead of failing on missing key

**Old**: If key does not exist → `store.update()` returns `False`.

**New**: If key does not exist → creates a new row with `value_type="string"` (the default
parameter value), ignoring whatever type the caller passed.

**Impact**: Silent data creation when a setting key is misspelled or doesn't exist yet.

---

## `owid_charts_service.py`

### 🔴 BUG 8 — `list_published_charts` returns a Query object, not a list

**Old**: `store.list_published()` → `List[OwidChartRecord]`

**New**:
```python
return session.query(OwidChartRecord).filter(OwidChartRecord.is_published == 1)
# 🔴 missing .all() — returns a Query, not a list
```

**Impact**: The owid charts route does `for c in list_published_charts()` — iterating a
detached Query outside its session raises `DetachedInstanceError` or returns wrong data.
`len(result)` would fail, and `to_dict()` on Query rows fetched outside the session will
raise `DetachedInstanceError`.

**Fix**: Add `.all()`.

---

### 🟡 DIFFERENCE 9 — `list_charts` no longer queries the join view

**Old**: queries `owid_charts_templates` JOIN `owid_charts` (a MySQL view that enriches
chart rows with their linked template title/id).

**New**: queries `OwidChartRecord` directly — only the `owid_charts` table. The
`template_title`, `template_id` fields on chart records will be `None` for all rows
unless the ORM model's `OwidChartRecord` maps to the view (needs verification).

---

### 🟡 DIFFERENCE 10 — `update_chart_data` skips falsy values

**Old** (`db_OwidCharts.update_chart_data`): updates field `if value is not None`.

**New**:
```python
for key, value in chart_data.items():
    if value:        # 🟡 skips falsy: 0, False, "", [] — can't set is_published=0
        setattr(chart, key, value)
```

**Impact**: Cannot set `is_published=0`, `has_map_tab=0`, `has_timeline=0` via
`update_chart_data`. Setting a chart to unpublished would silently be ignored.

---

## `template_service.py`

### 🟡 DIFFERENCE 11 — `list_templates` now sorts by title

**Old**: no ORDER BY — returns rows in DB insertion order.

**New**: `ORDER BY title` — alphabetical order.

**Impact**: Visual ordering change in admin/public template lists. No functional bug,
but any test asserting on list order will fail.

---

### 🟡 DIFFERENCE 12 — `list_templates(limit=...)` limit is silently dropped

**New**:
```python
query = session.query(TemplateRecord).order_by(TemplateRecord.title)
if limit:
    query.limit(limit)   # 🟡 result not reassigned — limit is lost
return query.all()
```

Same pattern as `list_jobs` bug #2. The `limit` parameter is accepted but has no effect.

---

### 🟡 DIFFERENCE 13 — `update_template_data` skips falsy values

Same as `update_chart_data` bug #10:
```python
for key, value in template_data.items():
    if value:   # 🟡 skips 0, False, "" — can't clear a field by setting it to ""
        setattr(template, key, value)
```

**Impact**: Cannot clear `last_world_file`, `last_world_year`, `source` etc. by passing
an empty string. Old code delegated to `store.update_template_data()` which used
`if value is not None`.

---

## `admin_service.py`

### 🟡 DIFFERENCE 14 — `set_coordinator_active` raises `AttributeError` if ID not found

**Old**: `record = store.get_by_id(coordinator_id)` raises `LookupError` if not found,
then `if record:` guards the update.

**New**:
```python
record = session.query(AdminUserRecord).filter(...).first()
record.is_active = is_active   # 🟡 no None check — AttributeError if record is None
```

---

### 🟡 DIFFERENCE 15 — `active_coordinators` filter uses ORM boolean coercion

**Old**: `[u.username for u in store.list() if u.is_active]` — Python truthiness on
the `is_active` value read from MySQL (could be `1`/`0` int).

**New**: `.filter(AdminUserRecord.is_active)` — SQLAlchemy ORM WHERE clause on the
`is_active` column. Functionally equivalent for boolean columns, but behaves
differently if the column stores `0`/`1` integers (SQLite `INTEGER` vs MySQL `TINYINT`).

---

## `user_token_service.py`

### 🟡 DIFFERENCE 16 — `upsert_user_token` raises `ValueError` on blank username

**Old**: no validation, inserts whatever username is given.

**New**:
```python
username = username.strip()
if not username:
    raise ValueError("Username is required")  # 🟡 new guard — callers don't expect this
```

**Impact**: If any caller passes an empty username (e.g. during OAuth callback edge case),
old code silently stored it; new code raises `ValueError` causing a 500.

---

### 🟡 DIFFERENCE 17 — `upsert_user_token` sets `rotated_at` on every update

**Old**: `rotated_at = CURRENT_TIMESTAMP` only on `ON DUPLICATE KEY UPDATE` (i.e. updates).

**New**: `orm_obj.rotated_at = now` on every upsert including initial inserts.

**Impact**: New user tokens will have `rotated_at` set at creation, whereas old code left
it `NULL` on first insert.

---

### 🟡 DIFFERENCE 18 — `mark_token_used` removed

The old service exported `mark_token_used(user_id)`. The new service does not have it.

It is only referenced in a **commented-out** line in `db/models/users.py`, so this is
safe to drop — but worth noting.

---

## Summary table

| # | Severity | Module | Function | Issue |
|---|----------|--------|----------|-------|
| 1 | 🔴 BUG | jobs_service | `update_job_status` | Positional arg to keyword-only param → `TypeError` |
| 2 | 🔴 BUG | jobs_service | `list_jobs` | `query.filter()` result discarded — filter never applied |
| 3 | 🟡 DIFF | jobs_service | `cancel_job` | No status guard — cancels completed/failed jobs |
| 4 | 🟡 DIFF | owid_charts_service | `list_charts` | Hard limit of 100 rows (was unlimited) |
| 5 | 🔴 BUG | settings_service | `create_setting` | Returns ORM object not `bool`; no duplicate check |
| 6 | 🔴 BUG | settings_service | `update_setting` | `str(value)` instead of type-serialization; booleans/JSON stored wrong |
| 7 | 🔴 BUG | settings_service | `update_setting` | Upserts on missing key instead of returning `False` |
| 8 | 🔴 BUG | owid_charts_service | `list_published_charts` | Missing `.all()` — returns Query not list |
| 9 | 🟡 DIFF | owid_charts_service | `list_charts` | Queries base table, not join view |
| 10 | 🟡 DIFF | owid_charts_service | `update_chart_data` | `if value:` skips falsy — can't set fields to `0`/`False` |
| 11 | 🟡 DIFF | template_service | `list_templates` | Now returns results sorted by title |
| 12 | 🟡 DIFF | template_service | `list_templates` | `query.limit()` result discarded — limit never applied |
| 13 | 🟡 DIFF | template_service | `update_template_data` | `if value:` skips falsy — can't clear fields |
| 14 | 🟡 DIFF | admin_service | `set_coordinator_active` | No None guard — `AttributeError` if ID not found |
| 15 | 🟡 DIFF | admin_service | `active_coordinators` | ORM filter vs Python filter (minor SQLite vs MySQL coercion risk) |
| 16 | 🟡 DIFF | user_token_service | `upsert_user_token` | New `ValueError` on blank username |
| 17 | 🟡 DIFF | user_token_service | `upsert_user_token` | `rotated_at` set on insert (was NULL) |
| 18 | 🟢 SAFE | user_token_service | `mark_token_used` | Removed — only referenced in commented-out code |

**🔴 = will cause runtime errors or data corruption**
**🟡 = behaviour change, may cause test failures or subtle bugs**
**🟢 = safe to drop**
