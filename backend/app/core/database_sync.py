"""
Синхронная настройка подключения к базе данных PostgreSQL для быстрого запуска.
"""

from typing import Generator
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, DeclarativeBase, declared_attr
from sqlalchemy.pool import StaticPool

from app.core.config import settings

# Создание синхронного движка (для быстрого запуска)
_db_url = settings.database_url_sync
_common_kwargs = dict(echo=settings.DATABASE_ECHO, pool_pre_ping=True, pool_recycle=3600)

if _db_url.startswith("sqlite"):
    # Для тестов используем in-memory с StaticPool, чтобы делиться одним соединением
    if settings.ENVIRONMENT == "testing":
        engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            **_common_kwargs,
        )
    else:
        engine = create_engine(
            _db_url,
            connect_args={"check_same_thread": False},
            **_common_kwargs,
        )
else:
    engine = create_engine(_db_url, **_common_kwargs)

# Создание фабрики сессий
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""
    
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s"
        }
    )
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Автоматическое именование таблиц."""
        return cls.__name__.lower()


def get_db() -> Generator:
    """Получение сессии базы данных."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
