---
name: flask-soc-audit
description: >
    Analyze a Flask-SQLAlchemy project for Separation of Concerns (SoC) violations
    and generate a structured audit report. Use this skill whenever the user wants
    to review, audit, or report on architectural issues in a Flask project — especially
    when they mention SoC, layering violations, fat routes, business logic in models,
    direct DB access from views, or any concern about code organization in Flask apps.
    Also trigger when the user shares a Flask project structure and asks for an
    architectural review, code quality report, or refactoring suggestions.
---

# Flask SoC Audit Skill

Produces a detailed **Separation of Concerns audit report** for a Flask-SQLAlchemy
project by statically analyzing the codebase layer by layer.

---

## Layers & Their Responsibilities

Before scanning, internalize the expected responsibilities of each layer:

| Layer               | Path Pattern       | Allowed Responsibilities                                                      |
| ------------------- | ------------------ | ----------------------------------------------------------------------------- |
| **Routes / Views**  | `public/`      | HTTP request parsing, input validation, calling services, returning responses |
| **Services**        | `db/services/`     | Business logic, orchestration between models, transactions                    |
| **Models**          | `db/models/`       | Data structure, relationships, simple computed properties                     |
| **Core / Utils**    | `core/`, `utils/`  | Reusable helpers with no Flask/DB dependencies                                |
| **Config**          | `config/`          | Settings, constants, environment config only                                  |
| **Background Jobs** | `background_jobs/` | Async task logic; must not import route-level code                            |
| **API Services**    | `api_services/`    | External HTTP calls; no DB access                                             |
| **Extensions**      | `extensions.py`    | Flask extension initialization only                                           |

---

## Step-by-Step Workflow

### 1. Discover the Project

```bash
find . -name "*.py" | sort
```

-   Map every `.py` file to its layer using the table above.
-   Note any files that live in unexpected locations.

### 2. Scan Each File for SoC Violations

For **every Python file**, check the import statements and code body for the
violation patterns described in `references/violation-patterns.md`.

Read that file now before proceeding:
→ `references/violation-patterns.md`

### 3. Classify Each Finding

Assign each violation a severity:

| Severity        | Meaning                                                                                                          |
| --------------- | ---------------------------------------------------------------------------------------------------------------- |
| 🔴 **Critical** | Architecture fundamentally broken in this spot (e.g., raw SQL in a route, ORM query in a config file)            |
| 🟠 **High**     | Clear layering violation that will cause maintainability pain (e.g., business logic in a model method)           |
| 🟡 **Medium**   | Questionable coupling that could be refactored (e.g., a service importing from `core` when a util would suffice) |
| 🟢 **Low**      | Minor style or convention issue (e.g., a route doing trivial formatting instead of a jinja filter)               |

### 4. Generate the Report

Use the report template in `references/report-template.md`.

Produce the report as a **Markdown file** saved to the project root:
`SOC_AUDIT_REPORT.md`

Also print a summary table to the terminal.

### 5. Suggest Refactors

For every Critical or High finding, add a concrete **"How to fix"** block in the
report with:

-   The offending code snippet (trimmed, ≤15 lines)
-   The suggested refactored version
-   Which layer the logic should move to

---

## Key Heuristics

-   **Route files** should contain almost no `if`/`for` logic beyond input validation.
    If a route function is >30 lines, flag it.
-   **Model files** should not import from `services/` or `public/`. Any method
    on a model that queries _other_ models is a violation.
-   **Services** are allowed to import models but must not import from `public/`.
-   **`core/` and `utils/`** must have zero Flask app-context dependencies (`current_app`,
    `g`, `request`) unless explicitly documented as Flask-aware utilities.
-   **`background_jobs/`** workers must not import from `public/`; they may
    import services.
-   **`config/`** must not instantiate anything — only define classes/dicts/constants.
-   **`extensions.py`** must only call `ext = ExtensionClass()` — no configuration logic.
-   **Circular imports** are a symptom of SoC violations; flag every one found.

---

## Output Requirements

-   Save report to `SOC_AUDIT_REPORT.md` in the project root.
-   Print a one-line summary per file scanned to stdout.
-   Print a final summary: total files scanned, findings by severity, top 3 most
    problematic files.

---

## References

-   `references/violation-patterns.md` — Exhaustive list of detectable violation patterns
-   `references/report-template.md` — Markdown template for the final report
-   `scripts/find_imports.sh` — Quick shell helper to grep cross-layer imports
