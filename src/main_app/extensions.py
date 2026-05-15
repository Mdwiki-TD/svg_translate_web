"""
Flask extensions instantiation.

IMPORTANT: This file must NOT import any application modules.
Only third-party extensions should be instantiated here.
This prevents circular imports when models/services import `db`.
"""

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# expire_on_commit=False preserves current behavior where objects
# remain accessible after commit without triggering new queries.
# (The existing engine.py uses sessionmaker(expire_on_commit=False))
db = SQLAlchemy(session_options={"expire_on_commit": False})
migrate = Migrate()
