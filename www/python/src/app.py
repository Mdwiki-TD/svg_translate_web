"""
# isort:skip_file
WSGI production entry point for the app.
"""

from __future__ import annotations
import logging
import sys
from pathlib import Path
import pymysql

sys.path.insert(0, str(Path(__file__).parent))
pymysql.install_as_MySQLdb()

# Hide standard HTTP access logs (200 / 304) from Werkzeug
logging.getLogger("werkzeug").setLevel(logging.ERROR)

from main_app import AppFactory  # noqa: E402

app = AppFactory.create()

if __name__ == "__main__":
    app.run(debug=False, port=5000)
