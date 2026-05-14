"""
# isort:skip_file
WSGI production entry point for the app.
"""

from __future__ import annotations
import logging
import pymysql

pymysql.install_as_MySQLdb()

# environment variables in production already in toolforge envvars no need to run load_dotenv()

from main_app import create_app  # noqa: E402
from main_app.config import DevelopmentConfig  # noqa: E402
from logger_config import configure_logging  # noqa: E402

configure_logging(logging.WARNING)

app = create_app(DevelopmentConfig)

if __name__ == "__main__":
    app.run(debug=False, port=5000)
