"""
Модель денежных потоков (Cashflow).
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Cashflow(Base):
    """Модель денежных потоков."""
    
    __tablename__ = "cashflows"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    amount = Column(Numeric(precision=15, scale=2), nullable=False)
    currency = Column(String(3), nullable=False, default="RUB")
    type = Column(String(50), nullable=False)  # deposit, withdrawal, dividend, etc.
    description = Column(Text)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    portfolio = relationship("Portfolio", back_populates="cashflows")
