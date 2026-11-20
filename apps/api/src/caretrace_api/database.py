from collections.abc import Iterator
from contextlib import contextmanager
from sqlite3 import Connection

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Database:
    def __init__(self, url: URL) -> None:
        if url.get_backend_name() == "sqlite":
            self.engine = _sqlite_engine(url)
        else:
            self.engine = create_engine(
                url,
                hide_parameters=True,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 3},
            )
        self._sessions = sessionmaker(bind=self.engine, expire_on_commit=False)

    @contextmanager
    def session(self) -> Iterator[Session]:
        with self._sessions.begin() as session:
            yield session

    def is_ready(self) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except SQLAlchemyError:
            return False
        return True

    def dispose(self) -> None:
        self.engine.dispose()


def _sqlite_engine(url: URL) -> Engine:
    if url.database in (None, "", ":memory:"):
        engine = create_engine(
            url,
            hide_parameters=True,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
    else:
        engine = create_engine(url, hide_parameters=True)

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection: Connection, _: object) -> None:
        cursor = connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()

    return engine
