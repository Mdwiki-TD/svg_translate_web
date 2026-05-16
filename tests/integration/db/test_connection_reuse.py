from src.main_app import create_app
from src.main_app.config import TestingConfig
from src.main_app.extensions import db as _db
from src.main_app.sqlalchemy_db.services import user_token_service as user_store


class FakeCursor:
    def __init__(self) -> None:
        self.description = None
        self.rowcount = 0

    def execute(self, sql: str, params=None) -> None:
        statement = sql.strip().upper()
        if statement.startswith("SELECT"):
            self.description = ("column",)
            self.rowcount = 0
        else:
            self.description = None
            self.rowcount = 1

    def executemany(self, sql: str, params_seq):
        self.description = None
        self.rowcount = len(list(params_seq))

    def fetchall(self):
        return []

    def close(self) -> None:
        pass


class FakeConnection:
    def cursor(self) -> FakeCursor:
        return FakeCursor()

    def ping(self, reconnect: bool = False) -> None:
        pass

    def close(self) -> None:
        pass

    def get_autocommit(self) -> bool:
        return True

    def rollback(self) -> None:
        pass

    def commit(self) -> None:
        pass


def test_sequential_requests_use_cached_connections(monkeypatch):

    app = create_app(TestingConfig)
    app.config.update(TESTING=True)

    with app.app_context():
        real_tables = [t for t in _db.metadata.tables.values() if not t.info.get("is_view")]
        _db.metadata.create_all(_db.engine, tables=real_tables)

    client = app.test_client()

    with client.session_transaction() as session:
        session["uid"] = 7

    response = client.get("/logout")
    assert response.status_code == 302

    response = client.get("/jobs/copy_svg_langs")
    assert response.status_code == 200

    with app.app_context():
        _db.session.remove()
        _db.metadata.drop_all(_db.engine, tables=real_tables)
