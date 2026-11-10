"""
# isort:skip_file
WSGI production entry point for the app.
"""

from __future__ import annotations
import sys
from pathlib import Path
import pymysql

sys.path.insert(0, str(Path(__file__).parent))
pymysql.install_as_MySQLdb()

from main_app import AppFactory  # noqa: E402

app = AppFactory.create()

if __name__ == "__main__":
    app.run(debug=False, port=5000)
