"""
Модель счета (брокерского, банковского и т.д.) для сервиса учета инвестиций.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, DECIMAL,
    ForeignKey, JSON, Enum, CheckConstraint, Index
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
import enum

from app.core.database_sync import Base


class AccountType(str, enum.Enum):
    """Типы счетов."""
    BROKER = "broker"
    IRA = "ira"
    PENSION = "pension"
    SAVINGS = "savings"
    CHECKING = "checking"
    CRYPTO_EXCHANGE = "crypto_exchange"
    OTHER = "other"


class Account(Base):
    """Модель инвестиционного счета."""
    
    __tablename__ = "accounts"
    
    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    portfolio_id: Mapped[int] = mapped_column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    
    # Информация о счете
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    broker: Mapped[Optional[str]] = mapped_column(String(100))
    account_number: Mapped[Optional[str]] = mapped_column(String(100))
    account_type: Mapped[AccountType] = mapped_column(Enum(AccountType), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)
    
    # Описание и настройки
    description: Mapped[Optional[str]] = mapped_column(Text)
    settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Статус
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_tax_advantaged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Кэшированные значения
    total_value: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 4))
    cash_balance: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 4))
    
    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Отношения
    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="accounts")
    
    # Ограничения и индексы
    __table_args__ = (
        Index('ix_accounts_portfolio_active', 'portfolio_id', 'is_active'),
        Index('ix_accounts_broker', 'broker'),
        CheckConstraint('length(name) >= 1', name='ck_accounts_name_not_empty'),
        CheckConstraint('currency ~ "^[A-Z]{3}$"', name='ck_accounts_currency_format'),
    )
    
    def __repr__(self) -> str:
        return f"<Account(id={self.id}, name='{self.name}', broker='{self.broker}')>"
