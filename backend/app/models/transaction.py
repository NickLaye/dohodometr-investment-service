"""Модель транзакции."""

from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlalchemy import Integer, String, DateTime, DECIMAL, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
import enum

from app.core.database_sync import Base


class TransactionType(str, enum.Enum):
    """Типы транзакций."""
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    COUPON = "coupon"
    TAX = "tax"
    FEE = "fee"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    SPLIT = "split"
    SPIN_OFF = "spin_off"
    MERGER = "merger"


class Transaction(Base):
    """Модель транзакции."""
    
    __tablename__ = "transactions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    instrument_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("instruments.id"), index=True)
    
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    
    quantity: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 8))
    price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 8))
    gross: Mapped[Decimal] = mapped_column(DECIMAL(20, 4), nullable=False)
    fee: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 4))
    tax: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 4))
    
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    fx_rate: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 8))
    
    meta: Mapped[Optional[str]] = mapped_column(Text)  # JSON
    lot_link: Mapped[Optional[str]] = mapped_column(String(100))  # Для FIFO
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, type={self.transaction_type}, gross={self.gross})>"
