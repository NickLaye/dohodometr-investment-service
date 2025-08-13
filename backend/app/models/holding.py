"""
Модель позиции (холдинга) в портфеле.
"""

from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlalchemy import Integer, DECIMAL, ForeignKey, DateTime, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database_sync import Base


class Holding(Base):
    """Модель позиции в портфеле."""
    
    __tablename__ = "holdings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    instrument_id: Mapped[int] = mapped_column(Integer, ForeignKey("instruments.id"), nullable=False, index=True)
    
    # Количество и средняя цена
    quantity: Mapped[Decimal] = mapped_column(DECIMAL(20, 8), nullable=False)
    avg_price: Mapped[Decimal] = mapped_column(DECIMAL(20, 8), nullable=False)
    currency: Mapped[str] = mapped_column(nullable=False)
    
    # Временные метки
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Отношения (временно закомментированы)
    # account: Mapped["Account"] = relationship("Account", back_populates="holdings")
    # instrument: Mapped["Instrument"] = relationship("Instrument")
    
    # Ограничения и индексы
    __table_args__ = (
        # Уникальная позиция на инструмент в рамках счета
        Index('ix_holdings_account_instrument', 'account_id', 'instrument_id', unique=True),
        
        # Проверочные ограничения
        CheckConstraint('quantity >= 0', name='ck_holdings_quantity_positive'),
        CheckConstraint('avg_price > 0', name='ck_holdings_avg_price_positive'),
    )
    
    def __repr__(self) -> str:
        return f"<Holding(account_id={self.account_id}, instrument_id={self.instrument_id}, quantity={self.quantity})>"
