"""
Репозиторий для работы с портфелями.
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, update, delete, and_, func

from app.models.portfolio import Portfolio, PortfolioSnapshot
from app.schemas.portfolio import PortfolioCreate, PortfolioUpdate
from app.models.account import Account
from app.core.logging import logger


class PortfolioRepository:
    """Репозиторий для работы с портфелями."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(
        self,
        data: PortfolioCreate,
        user_id: int,
        **kwargs
    ) -> Portfolio:
        """Создание нового портфеля из схемы."""
        try:
            portfolio = Portfolio(
                owner_id=user_id,
                name=data.name.strip(),
                base_currency=data.base_currency,
                description=data.description.strip() if data.description else None,
                **kwargs
            )
            
            self.db.add(portfolio)
            self.db.commit()
            self.db.refresh(portfolio)
            
            logger.info(f"Создан портфель: {portfolio.name} для пользователя {user_id}")
            return portfolio
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка создания портфеля {name}: {e}")
            raise
    
    def get_by_id(self, portfolio_id: int) -> Optional[Portfolio]:
        """Получение портфеля по ID."""
        stmt = select(Portfolio).where(Portfolio.id == portfolio_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    def get_by_id_with_accounts(self, portfolio_id: int) -> Optional[Portfolio]:
        """Получение портфеля с загруженными счетами."""
        stmt = (
            select(Portfolio)
            .options(selectinload(Portfolio.accounts))
            .where(Portfolio.id == portfolio_id)
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    def get_by_user_id(
        self,
        user_id: int,
        is_active: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> List[Portfolio]:
        """Получение портфелей пользователя."""
        stmt = select(Portfolio).where(Portfolio.owner_id == user_id)
        
        if is_active:
            stmt = stmt.where(Portfolio.is_active == True)
        
        stmt = stmt.order_by(Portfolio.created_at.desc()).offset(offset).limit(limit)
        
        result = self.db.execute(stmt)
        return result.scalars().all()
    
    def update(self, portfolio_id: int, data: PortfolioUpdate) -> Optional[Portfolio]:
        """Обновление портфеля из схемы."""
        # Исключаем поля, которые нельзя обновлять напрямую
        excluded_fields = {'id', 'owner_id', 'created_at', 'total_value', 'total_cost', 'total_pnl'}
        input_dict = data.dict(exclude_none=True)
        update_data = {k: v for k, v in input_dict.items() if k not in excluded_fields}
        
        if not update_data:
            return self.get_by_id(portfolio_id)
        
        update_data['updated_at'] = datetime.utcnow()
        
        stmt = update(Portfolio).where(Portfolio.id == portfolio_id).values(**update_data)
        self.db.execute(stmt)
        self.db.commit()
        
        return self.get_by_id(portfolio_id)
    
    def delete(self, portfolio_id: int) -> bool:
        """Мягкое удаление портфеля."""
        stmt = update(Portfolio).where(Portfolio.id == portfolio_id).values(
            is_active=False,
            updated_at=datetime.utcnow()
        )
        result = self.db.execute(stmt)
        self.db.commit()
        
        return result.rowcount > 0
    
    def hard_delete(self, portfolio_id: int) -> bool:
        """Жесткое удаление портфеля (для GDPR)."""
        stmt = delete(Portfolio).where(Portfolio.id == portfolio_id)
        result = self.db.execute(stmt)
        self.db.commit()
        
        return result.rowcount > 0
    
    def update_metrics(
        self,
        portfolio_id: int,
        total_value: Decimal,
        total_cost: Decimal,
        total_pnl: Decimal,
        **additional_metrics
    ):
        """Обновление кэшированных метрик портфеля."""
        update_data = {
            'total_value': total_value,
            'total_cost': total_cost,
            'total_pnl': total_pnl,
            'total_pnl_percent': (total_pnl / total_cost * 100) if total_cost > 0 else None,
            'metrics_calculated_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            **additional_metrics
        }
        
        stmt = update(Portfolio).where(Portfolio.id == portfolio_id).values(**update_data)
        self.db.execute(stmt)
        self.db.commit()
    
    def get_portfolio_summary(self, portfolio_id: int) -> Dict[str, Any]:
        """Получение сводки по портфелю."""
        portfolio = self.get_by_id(portfolio_id)
        if not portfolio:
            return {}
        
        # Получаем количество счетов
        accounts_count_stmt = (
            select(func.count(Account.id))
            .where(and_(Account.portfolio_id == portfolio_id, Account.is_active == True))
        )
        accounts_count_result = self.db.execute(accounts_count_stmt)
        accounts_count = accounts_count_result.scalar() or 0
        
        # Получаем общую стоимость cash балансов
        cash_balance_stmt = (
            select(func.coalesce(func.sum(Account.cash_balance), 0))
            .where(and_(Account.portfolio_id == portfolio_id, Account.is_active == True))
        )
        cash_balance_result = self.db.execute(cash_balance_stmt)
        total_cash = cash_balance_result.scalar() or Decimal('0')
        
        return {
            'id': portfolio.id,
            'name': portfolio.name,
            'base_currency': portfolio.base_currency,
            'accounts_count': accounts_count,
            'total_value': portfolio.total_value or Decimal('0'),
            'total_cost': portfolio.total_cost or Decimal('0'),
            'total_pnl': portfolio.total_pnl or Decimal('0'),
            'total_pnl_percent': portfolio.total_pnl_percent or Decimal('0'),
            'total_cash': total_cash,
            'daily_return': portfolio.daily_return,
            'monthly_return': portfolio.monthly_return,
            'yearly_return': portfolio.yearly_return,
            'twr_1m': portfolio.twr_1m,
            'twr_3m': portfolio.twr_3m,
            'twr_1y': portfolio.twr_1y,
            'xirr': portfolio.xirr,
            'volatility': portfolio.volatility,
            'sharpe_ratio': portfolio.sharpe_ratio,
            'max_drawdown': portfolio.max_drawdown,
            'metrics_calculated_at': portfolio.metrics_calculated_at,
            'created_at': portfolio.created_at,
            'updated_at': portfolio.updated_at
        }
    
    def create_snapshot(
        self,
        portfolio_id: int,
        snapshot_date: datetime,
        total_value: Decimal,
        total_cost: Decimal,
        total_pnl: Decimal,
        positions_count: int = 0,
        asset_allocation: Optional[Dict[str, Any]] = None,
        top_positions: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> PortfolioSnapshot:
        """Создание снимка портфеля."""
        try:
            snapshot = PortfolioSnapshot(
                portfolio_id=portfolio_id,
                snapshot_date=snapshot_date,
                total_value=total_value,
                total_cost=total_cost,
                total_pnl=total_pnl,
                positions_count=positions_count,
                asset_allocation=asset_allocation,
                top_positions=top_positions,
                **kwargs
            )
            
            self.db.add(snapshot)
            self.db.commit()
            self.db.refresh(snapshot)
            
            return snapshot
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка создания снимка портфеля {portfolio_id}: {e}")
            raise
    
    def get_snapshots(
        self,
        portfolio_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 365
    ) -> List[PortfolioSnapshot]:
        """Получение снимков портфеля за период."""
        stmt = (
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.portfolio_id == portfolio_id)
        )
        
        if start_date:
            stmt = stmt.where(PortfolioSnapshot.snapshot_date >= start_date)
        
        if end_date:
            stmt = stmt.where(PortfolioSnapshot.snapshot_date <= end_date)
        
        stmt = stmt.order_by(PortfolioSnapshot.snapshot_date.desc()).limit(limit)
        
        result = self.db.execute(stmt)
        return result.scalars().all()
    
    def get_public_portfolios(
        self,
        limit: int = 20,
        offset: int = 0
    ) -> List[Portfolio]:
        """Получение публичных портфелей."""
        stmt = (
            select(Portfolio)
            .where(and_(Portfolio.is_public == True, Portfolio.is_active == True))
            .order_by(Portfolio.total_value.desc().nullslast())
            .offset(offset)
            .limit(limit)
        )
        
        result = self.db.execute(stmt)
        return result.scalars().all()
    
    def search_portfolios(
        self,
        user_id: int,
        query: str,
        limit: int = 20
    ) -> List[Portfolio]:
        """Поиск портфелей пользователя."""
        stmt = (
            select(Portfolio)
            .where(
                and_(
                    Portfolio.owner_id == user_id,
                    Portfolio.is_active == True,
                    Portfolio.name.ilike(f"%{query}%")
                )
            )
            .order_by(Portfolio.updated_at.desc())
            .limit(limit)
        )
        
        result = self.db.execute(stmt)
        return result.scalars().all()
