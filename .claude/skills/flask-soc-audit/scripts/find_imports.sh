#!/usr/bin/env bash
# find_imports.sh — Quick cross-layer import scanner for Flask-SQLAlchemy projects
#
# Usage:
#   bash scripts/find_imports.sh [project_root]
#
# Prints lines where one layer imports from a layer it should not depend on.

ROOT="${1:-.}"

echo "=== Cross-Layer Import Scan ==="
echo "Root: $ROOT"
echo ""

# Routes importing models directly (should go through services)
echo "--- Routes → Models (V-R3) ---"
grep -rn "from.*db\.models\|import.*db\.models" "$ROOT/main_app/app_routes" 2>/dev/null || echo "(none)"

# Routes calling db.session directly (V-R2)
echo ""
echo "--- Routes → db.session (V-R2) ---"
grep -rn "db\.session\|\.query\." "$ROOT/main_app/app_routes" 2>/dev/null || echo "(none)"

# Models importing services (V-M1 / inverted dependency)
echo ""
echo "--- Models → Services (inverted) ---"
grep -rn "from.*services\|import.*services" "$ROOT/main_app/db/models" 2>/dev/null || echo "(none)"

# Models using Flask context (V-M3)
echo ""
echo "--- Models → Flask context (V-M3) ---"
grep -rn "from flask import\|current_app\|from flask" "$ROOT/main_app/db/models" 2>/dev/null || echo "(none)"

# Services importing routes (V-S1)
echo ""
echo "--- Services → Routes (V-S1) ---"
grep -rn "from.*app_routes\|import.*app_routes" "$ROOT/main_app/db/services" 2>/dev/null || echo "(none)"

# Services using jsonify / abort (V-S2)
echo ""
echo "--- Services → Flask responses (V-S2) ---"
grep -rn "jsonify\|make_response\|abort" "$ROOT/main_app/db/services" 2>/dev/null || echo "(none)"

# Core/utils using db or Flask context (V-C1, V-C2)
echo ""
echo "--- Core/Utils → DB or Flask context (V-C1, V-C2) ---"
grep -rn "db\.session\|current_app\|from flask" "$ROOT/main_app/core" "$ROOT/main_app/utils" 2>/dev/null || echo "(none)"

# Config instantiating objects (V-CF1)
echo ""
echo "--- Config → object instantiation (V-CF1) ---"
grep -rn "= .*()$\|= .*(\s" "$ROOT/main_app/config" 2>/dev/null | grep -v "^.*#" | grep -v "class\|def\|super\|dict\|list\|tuple\|str\|int\|bool\|None\|True\|False" || echo "(none)"

# Background workers importing routes (V-BG1)
echo ""
echo "--- Background Jobs → Routes (V-BG1) ---"
grep -rn "from.*app_routes\|import.*app_routes" "$ROOT/main_app/background_jobs" 2>/dev/null || echo "(none)"

# Workers missing app context (V-BG3) — heuristic
echo ""
echo "--- Background Jobs: db.session without app_context (V-BG3 heuristic) ---"
for f in $(find "$ROOT/main_app/background_jobs" -name "*.py" 2>/dev/null); do
  if grep -q "db\.session" "$f" && ! grep -q "app_context\|AppContext\|with app\." "$f"; then
    echo "  POSSIBLE: $f"
  fi
done
echo ""

# API services using db (V-API1)
echo ""
echo "--- API Services → DB (V-API1) ---"
grep -rn "db\.session\|\.query\." "$ROOT/main_app/api_services" 2>/dev/null || echo "(none)"

# os.getenv outside config (V-CF3)
echo ""
echo "--- os.getenv outside config/ (V-CF3) ---"
grep -rn "os\.getenv\|os\.environ" \
  "$ROOT/main_app/db" \
  "$ROOT/main_app/app_routes" \
  "$ROOT/main_app/core" \
  "$ROOT/main_app/background_jobs" \
  "$ROOT/main_app/api_services" \
  2>/dev/null || echo "(none)"

echo ""
echo "=== Scan complete. Review findings above and map to violation-patterns.md. ==="
