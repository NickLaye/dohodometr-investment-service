"""
Модели базы данных для сервиса учета инвестиций.
"""

from app.core.database_sync import Base
from app.core.config import settings

# Импортируем базовые модели (кросс-СУБД)
from . import (
    user,
    portfolio,
    account,
    holding,
    instrument,
    price,
    transaction,
    cashflow,
    benchmark,
    goal,
    alert,
    notification,
    broker_connection,
    tag,
    audit,
)

# Dialect-aware imports: избегаем PostgreSQL-специфичных типов (UUID/ENUM) на SQLite в тестах
_database_url = str(settings.DATABASE_URL or "")
_is_postgres = _database_url.startswith("postgresql")

if _is_postgres:
    from . import custom_asset, crypto_asset  # noqa: F401

__all__ = [
    "Base",
    "user",
    "portfolio", 
    "account",
    "holding",
    "instrument",
    "price",
    "transaction",
    "cashflow",
    "benchmark",
    "goal",
    "alert",
    "notification",
    "broker_connection",
    "tag",
    "audit",
]

if _is_postgres:
    __all__.extend(["custom_asset", "crypto_asset"])
