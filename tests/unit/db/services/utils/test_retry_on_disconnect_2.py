"""
Tests that reproduce the side effect flagged in review: calling
db.session.remove() inside retry_on_db_disconnect's retry loop discards
the scoped session, which detaches *any* other ORM object the caller
was holding in that same thread/request -- not just the one the
decorated function itself was working on.

These use a real in-memory SQLite database and a real scoped_session,
because DetachedInstanceError is a genuine SQLAlchemy object-state error
-- a MagicMock `db` can't reproduce it, it can only record that
.remove() was called.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base, relationship, scoped_session, sessionmaker
from sqlalchemy.orm.exc import DetachedInstanceError

from src.main_app.db.services.utils import retry_on_db_disconnect

import src.main_app.db.services.utils as decorators_module

Base = declarative_base()


class Author(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    books = relationship("Book", back_populates="author", lazy="select")


class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    author_id = Column(Integer, ForeignKey("authors.id"))
    author = relationship("Author", back_populates="books")


@pytest.fixture
def real_session(monkeypatch):
    """
    A real scoped_session backed by in-memory SQLite, patched in as the
    `db` used by the decorator -- standing in for Flask-SQLAlchemy's
    `db.session`, which is itself a scoped_session proxy.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = scoped_session(sessionmaker(bind=engine))

    fake_db = SimpleNamespace(session=SessionLocal)
    monkeypatch.setattr(decorators_module, "db", fake_db)

    yield SessionLocal

    SessionLocal.remove()
    engine.dispose()


@pytest.fixture
def seeded_author_id(real_session):
    """Insert one author with one book, return the author's id."""
    author = Author(name="Tolkien")
    author.books.append(Book(title="The Lord of the Rings"))
    real_session.add(author)
    real_session.commit()
    return author.id


def make_operational_error(message="some error", connection_invalidated=False):
    err = OperationalError(message, {}, Exception(message))
    err.connection_invalidated = connection_invalidated
    return err


def make_func(side_effect):
    func = MagicMock(side_effect=side_effect)
    func.__name__ = "fake_job_function"
    return func


class TestRetryDetachesUnrelatedSessionObjects:
    """
    Reproduces the exact scenario from the review comment: some *other*
    object, already loaded earlier in the same session, is held by the
    caller across the decorated call. After a retry, touching an
    unloaded attribute on that object blows up.
    """

    def test_other_loaded_object_becomes_detached_after_retry(
        self, real_session, seeded_author_id
    ):
        # Caller loads an object BEFORE calling the decorated function,
        # and has NOT yet touched its lazy relationship.
        author = real_session.query(Author).filter_by(id=seeded_author_id).one()
        assert "books" not in author.__dict__, "relationship must still be unloaded"

        # The decorated function itself has nothing to do with `author` --
        # it's just some other job that hits a transient disconnect.
        err = make_operational_error(connection_invalidated=True)
        func = make_func([err, "ok"])
        wrapped = retry_on_db_disconnect()(func)

        result = wrapped()
        assert result == "ok"  # the retry "succeeded" from the caller's POV

        # But the caller's earlier object is now unusable.
        with pytest.raises(DetachedInstanceError):
            author.books

    def test_even_already_loaded_scalar_attributes_become_inaccessible_after_retry(
        self, real_session, seeded_author_id
    ):
        """
        It's tempting to assume only *unloaded* attributes (like a lazy
        relationship) are at risk, and that data already pulled into
        memory is safe. That's not the case: Session.rollback() expires
        every attribute on every object in the session -- loaded or not
        -- as part of rolling back the transaction. Once .remove() then
        detaches the object, NOTHING on it can be refreshed anymore,
        including a plain scalar column that was read moments earlier.
        """
        author = real_session.query(Author).filter_by(id=seeded_author_id).one()
        assert author.name == "Tolkien"  # force-load the scalar column before the retry
        assert "name" in author.__dict__  # confirm it's actually sitting in memory

        err = make_operational_error(connection_invalidated=True)
        func = make_func([err, "ok"])
        wrapped = retry_on_db_disconnect()(func)
        wrapped()

        # rollback() (called before remove()) expired it despite being loaded...
        assert "name" not in author.__dict__
        # ...and remove() means it can never be refreshed again.
        with pytest.raises(DetachedInstanceError):
            author.name

    def test_rollback_alone_does_not_detach_objects(self, real_session, seeded_author_id):
        """
        Control test isolating the cause: db.session.rollback() expires
        objects but keeps them attached to the (still-open) session, so
        a subsequent lazy load works. The detachment is specifically a
        consequence of .remove(), not .rollback().
        """
        author = real_session.query(Author).filter_by(id=seeded_author_id).one()
        assert "books" not in author.__dict__

        real_session.rollback()  # same call the decorator makes first

        # No error: object is expired but still bound to an open session.
        assert [b.title for b in author.books] == ["The Lord of the Rings"]

    def test_retrying_function_observes_a_fresh_object_each_attempt(
        self, real_session, seeded_author_id
    ):
        """
        Shows the other half of the same root cause from the decorated
        function's own perspective: because .remove() tears down the
        scoped session, re-querying inside the retried call returns a
        *different* Python object than the one loaded on the failed
        attempt, even though it's the same database row.
        """
        seen_object_ids = []

        def load_and_maybe_fail():
            author = real_session.query(Author).filter_by(id=seeded_author_id).one()
            seen_object_ids.append(id(author))
            if len(seen_object_ids) == 1:
                raise make_operational_error(connection_invalidated=True)
            return author

        wrapped = retry_on_db_disconnect()(load_and_maybe_fail)
        wrapped()

        assert len(seen_object_ids) == 2
        assert seen_object_ids[0] != seen_object_ids[1], (
            "the session was torn down between attempts, so the retry "
            "loaded a brand-new instance instead of reusing identity map state"
        )
