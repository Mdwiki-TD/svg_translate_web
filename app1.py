"""
# isort:skip_file
WSGI development entry point for the app.
"""

from __future__ import annotations
import logging
import sys
import os
from pathlib import Path
import pymysql

# Set environment mode
os.environ["FLASK_ENV"] = "development"

# Ensure current directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent / "www/python"))

# Register PyMySQL driver
pymysql.install_as_MySQLdb()

# Initialize environment variables and external module paths before application setup
from src.bootstrap import EnvironmentInitializer  # noqa: E402
from src.logging_setup import ProcessLoggingConfigurator  # noqa: E402

# 1) .env first
_env_file_path = str(Path(__file__).resolve().parents[1] / ".env")
EnvironmentInitializer.setup(_env_file_path)

from src.main_app import AppFactory  # noqa: E402

# 2) Logging next, before the app exists (web: files + console, CLI: stderr only)

ProcessLoggingConfigurator.configure(
    debug=True,
    production=False,
    daily_rotation=True,
    name="src.main_app",
    set_root_level=False,
)

# 3) Third-party loggers
logging.getLogger("werkzeug").setLevel(logging.ERROR)  # Hide standard HTTP access logs (200 / 304) from Werkzeug
logging.getLogger("CopySVGTranslation").setLevel(logging.DEBUG)

# 4) Finally the app
app = AppFactory.create()

if __name__ == "__main__":
    try:
        app.run(debug=True, port=5000)
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received. Shutting down the application...")
        raise
