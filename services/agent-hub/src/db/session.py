"""Database session management for Agent Hub service.

Sets up SQLite database connection and session handling.
"""

import os
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.db.models import Base

# Database URL from environment or default to SQLite file
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///./data/agent-hub.db",
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database tables.

    Creates all tables defined in models if they don't exist.
    """
    # Ensure data directory exists for SQLite
    if "sqlite" in DATABASE_URL:
        db_path = DATABASE_URL.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Get database session.

    Yields a database session and ensures it's closed after use.
    Use as a FastAPI dependency.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Get database session as context manager.

    Use for non-FastAPI contexts.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
