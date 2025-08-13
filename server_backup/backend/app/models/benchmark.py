"""
Модель бенчмарков (Benchmark).
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text
from datetime import datetime

from app.core.database import Base


class Benchmark(Base):
    """Модель бенчмарков для сравнения."""
    
    __tablename__ = "benchmarks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)  # S&P 500, MOEX, etc.
    symbol = Column(String(20), nullable=False, unique=True)
    description = Column(Text)
    currency = Column(String(3), nullable=False, default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
