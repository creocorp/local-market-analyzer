"""Database engine, session factory, and schema initialisation.

Usage
-----
    from app.db.session import get_session, init_db

    # In FastAPI lifespan:
    init_db()  # creates tables if they don't exist

    # In endpoint / node:
    with get_session() as session:
        session.add(row)
        session.commit()

Database location
-----------------
The SQLite file is stored at ``backend/data/trading.db`` (outside the Python
package so it is not accidentally included in packages or Docker images).
The ``data/`` directory is created automatically on first run.

Switching to PostgreSQL
-----------------------
Replace the ``DATABASE_URL`` construction below with a ``postgresql+psycopg2://``
connection string.  Everything else — models, session usage — stays the same
because SQLModel/SQLAlchemy abstracts the dialect.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

# Import all models so that SQLModel.metadata knows about every table.
# Add new model imports here when you create new tables.
from app.db import models as _models  # noqa: F401 — side-effect import

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_DB_PATH = _DATA_DIR / "trading.db"

_DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_DB_PATH}")

# ``check_same_thread=False`` is required for SQLite when the engine is shared
# across async FastAPI workers.  It is ignored for other databases.
_connect_args = {"check_same_thread": False} if _DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(_DATABASE_URL, connect_args=_connect_args)


def init_db() -> None:
    """Create all tables that don't already exist.

    Safe to call on every startup — SQLAlchemy uses ``CREATE TABLE IF NOT EXISTS``.
    """
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Yield a SQLModel ``Session`` and commit/rollback automatically.

    Example::

        with get_session() as session:
            session.add(row)
            # commit happens automatically on clean exit
    """
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
