from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import event

from ..admin_api.models import Base
from .config import get_settings


settings = get_settings()
engine = create_engine(settings.database_url, future=True)

# Ensure search_path is set for every new DBAPI connection
@event.listens_for(engine, "connect")
def _set_search_path(dbapi_connection, connection_record):  # type: ignore[no-redef]
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute(f"SET search_path TO {settings.db_schema}, public")
        cursor.close()
    except Exception:
        # ignore on non-postgres drivers (e.g., sqlite in tests)
        pass
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    # Ensure dedicated schema exists and set default search_path
    schema = settings.db_schema
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        conn.execute(text(f"SET search_path TO {schema}, public"))
    Base.metadata.create_all(bind=engine, checkfirst=True)


@contextmanager
def session_scope() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Iterator[Session]:
    with session_scope() as session:
        yield session


