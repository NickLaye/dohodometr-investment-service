"""
Репозиторий для работы со счетами.
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, func
from sqlalchemy.orm import selectinload

from app.models.account import Account, AccountType
from app.core.logging import logger


class AccountRepository:
    """Репозиторий для работы со счетами."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
        self,
        portfolio_id: int,
        name: str,
        account_type: AccountType,
        currency: str = "RUB",
        broker: Optional[str] = None,
        account_number: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ) -> Account:
        """Создание нового счета."""
        try:
            account = Account(
                portfolio_id=portfolio_id,
                name=name.strip(),
                account_type=account_type,
                currency=currency,
                broker=broker.strip() if broker else None,
                account_number=account_number.strip() if account_number else None,
                description=description.strip() if description else None,
                **kwargs
            )
            
            self.db.add(account)
            await self.db.commit()
            await self.db.refresh(account)
            
            logger.info(f"Создан счет: {account.name} для портфеля {portfolio_id}")
            return account
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Ошибка создания счета {name}: {e}")
            raise
    
    async def get_by_id(self, account_id: int) -> Optional[Account]:
        """Получение счета по ID."""
        stmt = select(Account).where(Account.id == account_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_id_with_holdings(self, account_id: int) -> Optional[Account]:
        """Получение счета с загруженными холдингами."""
        stmt = (
            select(Account)
            .options(selectinload(Account.holdings))
            .where(Account.id == account_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_portfolio_accounts(
        self,
        portfolio_id: int,
        is_active: bool = True
    ) -> List[Account]:
        """Получение счетов портфеля."""
        stmt = select(Account).where(Account.portfolio_id == portfolio_id)
        
        if is_active:
            stmt = stmt.where(Account.is_active == True)
        
        stmt = stmt.order_by(Account.created_at.asc())
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def update(self, account_id: int, **kwargs) -> Optional[Account]:
        """Обновление счета."""
        # Исключаем поля, которые нельзя обновлять напрямую
        excluded_fields = {'id', 'portfolio_id', 'created_at', 'total_value', 'cash_balance'}
        update_data = {k: v for k, v in kwargs.items() if k not in excluded_fields}
        
        if not update_data:
            return await self.get_by_id(account_id)
        
        update_data['updated_at'] = datetime.utcnow()
        
        stmt = update(Account).where(Account.id == account_id).values(**update_data)
        await self.db.execute(stmt)
        await self.db.commit()
        
        return await self.get_by_id(account_id)
    
    async def delete(self, account_id: int) -> bool:
        """Мягкое удаление счета."""
        stmt = update(Account).where(Account.id == account_id).values(
            is_active=False,
            updated_at=datetime.utcnow()
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def hard_delete(self, account_id: int) -> bool:
        """Жесткое удаление счета (для GDPR)."""
        stmt = delete(Account).where(Account.id == account_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def update_totals(
        self,
        account_id: int,
        total_value: Decimal,
        cash_balance: Decimal
    ):
        """Обновление кэшированных значений счета."""
        stmt = update(Account).where(Account.id == account_id).values(
            total_value=total_value,
            cash_balance=cash_balance,
            updated_at=datetime.utcnow()
        )
        await self.db.execute(stmt)
        await self.db.commit()
    
    async def get_account_summary(self, account_id: int) -> Dict[str, Any]:
        """Получение сводки по счету."""
        account = await self.get_by_id(account_id)
        if not account:
            return {}
        
        # Получаем количество холдингов
        from app.models.holding import Holding
        holdings_count_stmt = (
            select(func.count(Holding.id))
            .where(Holding.account_id == account_id)
        )
        holdings_count_result = await self.db.execute(holdings_count_stmt)
        holdings_count = holdings_count_result.scalar() or 0
        
        # Получаем общую стоимость холдингов
        holdings_value_stmt = (
            select(func.coalesce(func.sum(Holding.quantity * Holding.avg_price), 0))
            .where(Holding.account_id == account_id)
        )
        holdings_value_result = await self.db.execute(holdings_value_stmt)
        holdings_value = holdings_value_result.scalar() or Decimal('0')
        
        return {
            'id': account.id,
            'name': account.name,
            'broker': account.broker,
            'account_type': account.account_type.value,
            'currency': account.currency,
            'is_active': account.is_active,
            'holdings_count': holdings_count,
            'holdings_value': float(holdings_value),
            'cash_balance': float(account.cash_balance or Decimal('0')),
            'total_value': float(account.total_value or Decimal('0')),
            'created_at': account.created_at.isoformat(),
            'updated_at': account.updated_at.isoformat()
        }
    
    async def search_accounts(
        self,
        portfolio_id: int,
        query: str,
        limit: int = 20
    ) -> List[Account]:
        """Поиск счетов в портфеле."""
        stmt = (
            select(Account)
            .where(
                and_(
                    Account.portfolio_id == portfolio_id,
                    Account.is_active == True,
                    Account.name.ilike(f"%{query}%")
                )
            )
            .order_by(Account.updated_at.desc())
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_accounts_by_broker(self, broker: str) -> List[Account]:
        """Получение счетов по брокеру."""
        stmt = (
            select(Account)
            .where(
                and_(
                    Account.broker.ilike(f"%{broker}%"),
                    Account.is_active == True
                )
            )
            .order_by(Account.created_at.desc())
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
