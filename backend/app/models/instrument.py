"""
Модель финансового инструмента.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, DateTime, Text, JSON, Enum, Boolean, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
import enum

from app.core.database_sync import Base


class InstrumentType(str, enum.Enum):
    """Типы финансовых инструментов."""
    EQUITY = "equity"
    BOND = "bond" 
    ETF = "etf"
    CURRENCY = "currency"
    COMMODITY = "commodity"
    CRYPTO = "crypto"
    CUSTOM = "custom"


class Instrument(Base):
    """Модель финансового инструмента."""
    
    __tablename__ = "instruments"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    figi: Mapped[Optional[str]] = mapped_column(String(12), index=True)
    mic: Mapped[Optional[str]] = mapped_column(String(10))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    instrument_type: Mapped[InstrumentType] = mapped_column(Enum(InstrumentType), nullable=False)
    sector: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[Optional[str]] = mapped_column(String(3))
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    lot: Mapped[int] = mapped_column(default=1, nullable=False)
    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('ix_instruments_ticker_mic', 'ticker', 'mic'),
        Index('ix_instruments_type_active', 'instrument_type', 'is_active'),
        CheckConstraint('lot > 0', name='ck_instruments_lot_positive'),
    )

    def __repr__(self) -> str:
        return f"<Instrument(id={self.id}, ticker='{self.ticker}', name='{self.name}')>"
