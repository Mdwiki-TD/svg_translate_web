"""
# isort:skip_file
WSGI production entry point for the app.
"""

from __future__ import annotations
import logging
import sys
from pathlib import Path
import pymysql

# Ensure current directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent))

# Register PyMySQL driver
pymysql.install_as_MySQLdb()

# Initialize environment variables and external module paths before application setup
from bootstrap import EnvironmentInitializer  # noqa: E402
from logging_setup import ProcessLoggingConfigurator  # noqa: E402

# 1) .env first
EnvironmentInitializer.setup()

from main_app import AppFactory  # noqa: E402
from main_app.config import ConfigLoader  # noqa: E402

# 2) Logging next, before the app exists (web: files + console, CLI: stderr only)
config_class = ConfigLoader.load()
settings = config_class()
ProcessLoggingConfigurator.configure(
    debug=bool(getattr(settings, "DEBUG", False)),
    production=bool(getattr(settings, "IS_PRODUCTION", False)),
)

# 3) Third-party loggers
logging.getLogger("werkzeug").setLevel(logging.ERROR)  # Hide standard HTTP access logs (200 / 304) from Werkzeug

# 4) Finally the app
app = AppFactory.create(config_class)

if __name__ == "__main__":
    app.run(debug=False, port=5000)
