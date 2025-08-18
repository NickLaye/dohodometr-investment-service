"""
Модель портфеля для сервиса учета инвестиций.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, DECIMAL,
    ForeignKey, JSON, CheckConstraint, Index
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database_sync import Base


class Portfolio(Base):
    """Модель инвестиционного портфеля."""
    
    __tablename__ = "portfolios"
    
    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Основная информация
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    base_currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)
    
    # Настройки портфеля
    settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Настройки приватности
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Вычисляемые поля (кэшируются)
    total_value: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 4))
    total_cost: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 4))
    total_pnl: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 4))
    total_pnl_percent: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 4))
    
    # Доходность (кэшируется)
    daily_return: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 6))
    weekly_return: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 6))
    monthly_return: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 6))
    yearly_return: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 6))
    
    # TWR и XIRR (кэшируются)
    twr_1m: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 6))
    twr_3m: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 6))
    twr_6m: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 6))
    twr_1y: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 6))
    twr_3y: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 6))
    twr_5y: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 6))
    twr_inception: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 6))
    
    xirr: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 6))
    
    # Метрики риска (кэшируются)
    volatility: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 6))
    sharpe_ratio: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 6))
    max_drawdown: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 6))
    
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
    
    # Время последнего пересчета метрик
    metrics_calculated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Отношения
    cashflows: Mapped[List["Cashflow"]] = relationship(
        "Cashflow",
        back_populates="portfolio",
        cascade="all, delete-orphan"
    )
    # Минимальная связь с пользователем для интеграционного теста
    user = relationship("User", primaryjoin="User.id==Portfolio.owner_id", viewonly=True)
    
    # Ограничения и индексы
    __table_args__ = (
        # Составной индекс для поиска портфелей пользователя
        Index('ix_portfolios_owner_active', 'owner_id', 'is_active'),
        
        # Индекс для публичных портфелей
        Index('ix_portfolios_public', 'is_public', 'is_active'),
        
        # Индекс для метрик
        Index('ix_portfolios_metrics_calculated', 'metrics_calculated_at'),
        
        # Проверочные ограничения
        CheckConstraint('length(name) >= 1', name='ck_portfolios_name_not_empty'),
        # SQLite не поддерживает ~ (regex), проверяем формат валюты на уровне схем/бизнес-логики
    )
    
    def __repr__(self) -> str:
        return f"<Portfolio(id={self.id}, name='{self.name}', owner_id={self.owner_id})>"

    # Алиас для совместимости со старыми вызовами (user_id == owner_id)
    @property
    def user_id(self) -> int:
        return self.owner_id
    @user_id.setter
    def user_id(self, value: int) -> None:
        self.owner_id = value

    # Совместимость: alias для поля currency
    @property
    def currency(self) -> str:
        return self.base_currency
    @currency.setter
    def currency(self, value: str) -> None:
        self.base_currency = value
    
    @property
    def pnl_percent(self) -> Optional[Decimal]:
        """Процент прибыли/убытка."""
        if self.total_cost and self.total_cost > 0 and self.total_pnl is not None:
            return (self.total_pnl / self.total_cost) * 100
        return None
    
    @property
    def is_profitable(self) -> bool:
        """Прибыльный ли портфель."""
        return self.total_pnl is not None and self.total_pnl > 0


class PortfolioSnapshot(Base):
    """Снимок портфеля на определенную дату для отслеживания истории."""
    
    __tablename__ = "portfolio_snapshots"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    portfolio_id: Mapped[int] = mapped_column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    
    # Дата снимка
    snapshot_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Значения на дату снимка
    total_value: Mapped[Decimal] = mapped_column(DECIMAL(20, 4), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(DECIMAL(20, 4), nullable=False)
    total_pnl: Mapped[Decimal] = mapped_column(DECIMAL(20, 4), nullable=False)
    
    # Количество позиций
    positions_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Распределение по классам активов (JSON)
    asset_allocation: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Топ-10 позиций (JSON)
    top_positions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Дивиденды и купоны за период
    dividends_received: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 4))
    coupons_received: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 4))
    
    # Метаданные
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Отношения
    portfolio: Mapped["Portfolio"] = relationship("Portfolio")
    
    # Ограничения и индексы
    __table_args__ = (
        # Уникальный снимок на дату для портфеля
        Index('ix_portfolio_snapshots_unique', 'portfolio_id', 'snapshot_date', unique=True),
        
        # Индекс для поиска по дате
        Index('ix_portfolio_snapshots_date', 'snapshot_date'),
        
        # Проверочные ограничения
        CheckConstraint('total_value >= 0', name='ck_snapshots_total_value_positive'),
        CheckConstraint('total_cost >= 0', name='ck_snapshots_total_cost_positive'),
        CheckConstraint('positions_count >= 0', name='ck_snapshots_positions_count_positive'),
    )
    
    def __repr__(self) -> str:
        return f"<PortfolioSnapshot(id={self.id}, portfolio_id={self.portfolio_id}, date={self.snapshot_date})>"


class PortfolioBenchmark(Base):
    """Связь портфеля с бенчмарками для сравнения."""
    
    __tablename__ = "portfolio_benchmarks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    portfolio_id: Mapped[int] = mapped_column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    benchmark_id: Mapped[int] = mapped_column(Integer, ForeignKey("benchmarks.id"), nullable=False, index=True)
    
    # Вес бенчмарка (для составных бенчмарков)
    weight: Mapped[Decimal] = mapped_column(DECIMAL(5, 4), default=Decimal('1.0000'), nullable=False)
    
    # Активность
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Отношения (временно закомментированы)
    # portfolio: Mapped["Portfolio"] = relationship("Portfolio")
    # benchmark: Mapped["Benchmark"] = relationship("Benchmark")
    
    # Ограничения и индексы
    __table_args__ = (
        # Уникальная связь портфель-бенчмарк
        Index('ix_portfolio_benchmarks_unique', 'portfolio_id', 'benchmark_id', unique=True),
        
        # Проверочные ограничения
        CheckConstraint('weight > 0 AND weight <= 1', name='ck_portfolio_benchmarks_weight_valid'),
    )
    
    def __repr__(self) -> str:
        return f"<PortfolioBenchmark(portfolio_id={self.portfolio_id}, benchmark_id={self.benchmark_id})>"
