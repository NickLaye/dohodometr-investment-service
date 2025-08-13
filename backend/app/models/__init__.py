"""
Модели базы данных для сервиса учета инвестиций.
"""

from app.core.database_sync import Base

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
    custom_asset,
    crypto_asset
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
    "custom_asset",
    "crypto_asset",
]
