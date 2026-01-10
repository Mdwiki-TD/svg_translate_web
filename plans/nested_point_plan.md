
## **Implementation Plan:  Fix Nested File Endpoint**

### **Overview**
Create a new route endpoint that allows users to submit a file name (e.g., `File: Dengue_fever_deaths,_2000_to_2021,_AGO.svg`), downloads it, fixes nested tags, and uploads it back to Wikimedia Commons.

---

### **Step 1: Create New Blueprint Route Module**

**Location**: `src/app/app_routes/fix_nested/`

Create the following files:

1. **`src/app/app_routes/fix_nested/__init__.py`**
   - Export the blueprint `bp_fix_nested`

2. **`src/app/app_routes/fix_nested/routes. py`**
   - Contains the main route handlers
   - Two endpoints:
     - `GET /fix_nested` - Display form to input file name
     - `POST /fix_nested` - Process the file fix request

---

### **Step 2: Route Handler Logic**

**File**:  `src/app/app_routes/fix_nested/routes.py`

#### **GET Route** (`/fix_nested`)
- Render a template with a form
- Form fields:
  - Text input for file name (with placeholder:  "File:Example.svg")
  - Submit button

#### **POST Route** (`/fix_nested`)
```python
from pathlib import Path
from flask import Blueprint, render_template, request, flash, redirect, url_for
from ... tasks.downloads. download import download_one_file
from CopySVGTranslation import match_nested_tags, fix_nested_file
from ...tasks.uploads.upload_bot import upload_file
from ...users.current import get_current_user
import logging

bp_fix_nested = Blueprint("fix_nested", __name__, url_prefix="/fix_nested")
logger = logging.getLogger("svg_translate")

@bp_fix_nested.route("/", methods=["GET", "POST"])
def fix_nested():
    ...
```

---

### **Step 3: Processing Function**

**File**: `src/app/app_routes/fix_nested/fix_utils.py`

```python

from pathlib import Path
from ...tasks.downloads.download import download_one_file
from CopySVGTranslation import match_nested_tags, fix_nested_file
from ...tasks.uploads.upload_bot import upload_file
import logging
import tempfile

logger = logging.getLogger("svg_translate")


def download_svg_file(filename: str, temp_dir: Path) -> dict:
    """Download SVG file and return file path or error info."""
    ...


def detect_nested_tags(file_path: Path) -> dict:
    """Detect nested tags in SVG file."""
    ...


def fix_nested_tags(file_path: Path) -> bool:
    """Fix nested tags in-place."""
    ...


def verify_fix(file_path: Path, before_count: int) -> dict:
    """Verify nested tags count after fix."""
    ...


def upload_fixed_svg(
    filename: str,
    file_path: Path,
    tags_fixed: int,
) -> dict:
    """Upload fixed SVG file to Commons."""
    ...


def process_fix_nested(filename: str) -> dict:
    """High-level orchestration for fixing nested SVG tags."""
    ...

```

---

### **Step 4: Create Template**

**File**: `src/templates/fix_nested/form.html`

```html
{% extends "base.html" %}

{% block title %}Fix Nested SVG Tags{% endblock %}

{% block content %}
<div class="container mt-2">
    ...
</div>
{% endblock %}
```

---

### **Step 5: Register Blueprint**

**Update**: `src/app/app_routes/__init__.py`

```python
from .auth. routes import bp_auth
from .main.routes import bp_main
from .explorer.routes import bp_explorer
from .templates.routes import bp_templates
from .cancel_restart.routes import bp_tasks_managers
from .tasks.routes import bp_tasks, close_task_store
from .admin.routes import bp_admin
from .fix_nested.routes import bp_fix_nested  # Add this

__all__ = [
    "bp_auth",
    "bp_main",
    "bp_explorer",
    "bp_templates",
    "bp_tasks",
    "bp_tasks_managers",
    "bp_admin",
    "bp_fix_nested",  # Add this
    "close_task_store",
]
```

**Update**: `src/app/__init__.py`

```python
from .app_routes import (
    bp_admin,
    bp_auth,
    bp_main,
    bp_tasks,
    bp_explorer,
    bp_templates,
    bp_tasks_managers,
    bp_fix_nested,  # Add this
    close_task_store,
)

# ... later in create_app() ...
app.register_blueprint(bp_fix_nested)  # Add this line
```

---

### **Step 6: Add Navigation Link (Optional)**

Add a link to the main navigation or admin panel to access `/fix_nested`.

---

### **Step 7: Error Handling Enhancements**

Add specific flash messages for:
- File not found on Commons
- Download failures
- No nested tags found
- Fix failed (file too complex, >10 nested levels)
- Upload failures (permissions, rate limits)
- Authentication errors

---

### **Step 8: Testing Plan**

1. **Unit Tests** (`tests/test_fix_nested.py`):
   - Test with valid file name
   - Test with "File:" prefix
   - Test with non-existent file
   - Test with file without nested tags
   - Test with file having nested tags

2. **Integration Tests**:
   - Mock download, fix, and upload functions
   - Test error scenarios

3. **Manual Testing**:
   - Test with actual Commons files
   - Verify upload permissions
   - Check flash messages

---

### **Summary of Files to Create/Modify**

#### **New Files**:
1. `src/app/app_routes/fix_nested/__init__.py`
2. `src/app/app_routes/fix_nested/routes.py`
3. `src/app/app_routes/fix_nested/fix_utils.py`
4. `src/templates/fix_nested/form.html`
5. `tests/test_fix_nested.py` (optional)

#### **Modified Files**:
1. `src/app/app_routes/__init__.py`
2. `src/app/__init__.py`

---

### **Additional Considerations**

1. **Rate Limiting**: Add rate limiting to prevent abuse
2. **Logging**: Comprehensive logging at each step
3. **User Authentication**: Ensure user is logged in before allowing fixes
4. **File Size Limits**: Consider adding max file size checks
5. **Queue System**: For large files, consider async processing
6. **Result History**: Store fix results in database for audit trail
