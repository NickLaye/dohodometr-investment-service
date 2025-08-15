"""
DB access compatibility layer for admin module and app.
Re-exports sync configuration from `database_sync`.
"""

from app.core.database_sync import Base, SessionLocal, engine, get_db

__all__ = [
    "Base",
    "SessionLocal",
    "engine",
    "get_db",
]


