"""Модель цен инструментов."""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Integer, DateTime, DECIMAL, ForeignKey, String, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Price(Base):
    """Модель цены инструмента."""
    
    __tablename__ = "prices"
    
    instrument_id: Mapped[int] = mapped_column(Integer, ForeignKey("instruments.id"), primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    close: Mapped[Decimal] = mapped_column(DECIMAL(20, 8), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    
    __table_args__ = (
        Index('ix_prices_ts', 'ts'),
        Index('ix_prices_instrument_ts', 'instrument_id', 'ts'),
    )
    
    def __repr__(self) -> str:
        return f"<Price(instrument_id={self.instrument_id}, ts={self.ts}, close={self.close})>"
