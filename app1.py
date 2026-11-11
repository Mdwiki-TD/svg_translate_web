"""
# isort:skip_file
WSGI development entry point for the app.
"""

from __future__ import annotations
import sys
import os
from pathlib import Path
import pymysql

# Set environment mode
os.environ["FLASK_ENV"] = "development"

# Ensure current directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent / "www/python/src"))

# Register PyMySQL driver
pymysql.install_as_MySQLdb()

# Initialize environment variables and external module paths before application setup
from bootstrap import EnvironmentInitializer  # Adjust import based on module location  # noqa: E402

_env_file_path = str(Path(__file__).resolve().parents[2] / ".env")

EnvironmentInitializer.setup(_env_file_path)

# import app here
from main_app.logger_config import configure_logging  # noqa: E402

configure_logging(
    10,  # DEBUG = 10
    use_colorlog=True,
    name="CopySVGTranslation",
)

from main_app import AppFactory  # noqa: E402

app = AppFactory.create()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
