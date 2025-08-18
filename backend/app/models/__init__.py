"""
Модели базы данных для сервиса учета инвестиций.
"""

from app.core.database_sync import Base

# В тестовой SQLite отключаем таблицы, завязанные на PostgreSQL типы (UUID/JSONB)
from .user import *
from .portfolio import *
from .account import *
from .instrument import *
from .price import *
from .transaction import *
from .cashflow import *
from .benchmark import *
# custom_asset модели также используют UUID/ENUM Postgres — исключаем из SQLite
# крипто-модели пропускаем для совместимости с SQLite

# Импортируем все модели для правильного создания таблиц
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
    # custom_asset,
    # crypto_asset,
)

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
    # "custom_asset",
    # "crypto_asset",
]
