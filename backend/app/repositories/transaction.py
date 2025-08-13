"""
Репозиторий для работы с транзакциями.
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, update, delete, and_, func, or_

from app.models.transaction import Transaction, TransactionType
from app.models.holding import Holding
from app.core.logging import logger


class TransactionRepository:
    """Репозиторий для работы с транзакциями."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(
        self,
        account_id: int,
        transaction_type: TransactionType,
        gross: Decimal,
        currency: str,
        ts: datetime,
        instrument_id: Optional[int] = None,
        quantity: Optional[Decimal] = None,
        price: Optional[Decimal] = None,
        fee: Optional[Decimal] = None,
        tax: Optional[Decimal] = None,
        fx_rate: Optional[Decimal] = None,
        meta: Optional[str] = None,
        **kwargs
    ) -> Transaction:
        """Создание новой транзакции."""
        try:
            transaction = Transaction(
                account_id=account_id,
                instrument_id=instrument_id,
                ts=ts,
                transaction_type=transaction_type,
                quantity=quantity,
                price=price,
                gross=gross,
                fee=fee or Decimal('0'),
                tax=tax or Decimal('0'),
                currency=currency,
                fx_rate=fx_rate,
                meta=meta,
                **kwargs
            )
            
            self.db.add(transaction)
            self.db.flush()  # Получаем ID без коммита
            
            # Обрабатываем FIFO логику для покупок/продаж
            if transaction_type in [TransactionType.BUY, TransactionType.SELL] and instrument_id:
                self._update_holdings_fifo(transaction)
            
            self.db.commit()
            self.db.refresh(transaction)
            
            logger.info(f"Создана транзакция {transaction_type} на сумму {gross} {currency}")
            return transaction
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка создания транзакции: {e}")
            raise
    
    def bulk_create(self, transactions_data: List[Dict[str, Any]]) -> List[Transaction]:
        """Массовое создание транзакций."""
        try:
            transactions = []
            for data in transactions_data:
                transaction = Transaction(**data)
                self.db.add(transaction)
                transactions.append(transaction)
            
            self.db.flush()  # Получаем ID для всех транзакций
            
            # Обрабатываем FIFO для всех транзакций с инструментами
            for transaction in transactions:
                if (transaction.transaction_type in [TransactionType.BUY, TransactionType.SELL] 
                    and transaction.instrument_id):
                    self._update_holdings_fifo(transaction)
            
            self.db.commit()
            
            for transaction in transactions:
                self.db.refresh(transaction)
            
            logger.info(f"Создано {len(transactions)} транзакций")
            return transactions
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка массового создания транзакций: {e}")
            raise
    
    def _update_holdings_fifo(self, transaction: Transaction):
        """Обновление холдингов с учетом FIFO логики."""
        if not transaction.instrument_id or not transaction.quantity:
            return
        
        # Получаем или создаем холдинг
        holding_stmt = select(Holding).where(
            and_(
                Holding.account_id == transaction.account_id,
                Holding.instrument_id == transaction.instrument_id
            )
        )
        result = self.db.execute(holding_stmt)
        holding = result.scalar_one_or_none()
        
        if transaction.transaction_type == TransactionType.BUY:
            if holding:
                # Обновляем существующий холдинг (средневзвешенная цена)
                total_value = (holding.quantity * holding.avg_price + 
                              transaction.quantity * transaction.price)
                total_quantity = holding.quantity + transaction.quantity
                new_avg_price = total_value / total_quantity if total_quantity > 0 else Decimal('0')
                
                holding.quantity = total_quantity
                holding.avg_price = new_avg_price
                holding.updated_at = datetime.utcnow()
            else:
                # Создаем новый холдинг
                holding = Holding(
                    account_id=transaction.account_id,
                    instrument_id=transaction.instrument_id,
                    quantity=transaction.quantity,
                    avg_price=transaction.price,
                    currency=transaction.currency
                )
                self.db.add(holding)
        
        elif transaction.transaction_type == TransactionType.SELL:
            if holding and holding.quantity >= transaction.quantity:
                # Уменьшаем количество (FIFO - средняя цена остается)
                holding.quantity -= transaction.quantity
                holding.updated_at = datetime.utcnow()
                
                # Если количество стало 0, удаляем холдинг
                if holding.quantity == 0:
                    self.db.delete(holding)
                
                # Генерируем FIFO lot_link для отслеживания
                transaction.lot_link = f"fifo_{holding.id}_{transaction.id}"
            else:
                # Ошибка: недостаточно инструментов для продажи
                raise ValueError(
                    f"Недостаточно инструментов для продажи. "
                    f"Доступно: {holding.quantity if holding else 0}, "
                    f"Требуется: {transaction.quantity}"
                )
    
    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """Получение транзакции по ID."""
        stmt = select(Transaction).where(Transaction.id == transaction_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    def get_account_transactions(
        self,
        account_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_types: Optional[List[TransactionType]] = None,
        instrument_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Transaction]:
        """Получение транзакций счета с фильтрами."""
        stmt = select(Transaction).where(Transaction.account_id == account_id)
        
        if start_date:
            stmt = stmt.where(Transaction.ts >= start_date)
        
        if end_date:
            stmt = stmt.where(Transaction.ts <= end_date)
        
        if transaction_types:
            stmt = stmt.where(Transaction.transaction_type.in_(transaction_types))
        
        if instrument_id:
            stmt = stmt.where(Transaction.instrument_id == instrument_id)
        
        stmt = stmt.order_by(Transaction.ts.desc()).offset(offset).limit(limit)
        
        result = self.db.execute(stmt)
        return result.scalars().all()
    
    def get_portfolio_transactions(
        self,
        portfolio_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **filters
    ) -> List[Transaction]:
        """Получение всех транзакций портфеля."""
        # Подзапрос для получения account_id портфеля
        from app.models.account import Account
        
        account_subquery = (
            select(Account.id)
            .where(Account.portfolio_id == portfolio_id)
            .subquery()
        )
        
        stmt = select(Transaction).where(
            Transaction.account_id.in_(select(account_subquery))
        )
        
        if start_date:
            stmt = stmt.where(Transaction.ts >= start_date)
        
        if end_date:
            stmt = stmt.where(Transaction.ts <= end_date)
        
        # Применяем дополнительные фильтры
        for key, value in filters.items():
            if hasattr(Transaction, key) and value is not None:
                stmt = stmt.where(getattr(Transaction, key) == value)
        
        stmt = stmt.order_by(Transaction.ts.desc())
        
        result = self.db.execute(stmt)
        return result.scalars().all()
    
    def update(self, transaction_id: int, **kwargs) -> Optional[Transaction]:
        """Обновление транзакции."""
        # Исключаем поля, которые нельзя обновлять
        excluded_fields = {'id', 'created_at'}
        update_data = {k: v for k, v in kwargs.items() if k not in excluded_fields}
        
        if not update_data:
            return self.get_by_id(transaction_id)
        
        # Получаем старую транзакцию для пересчета холдингов
        old_transaction = self.get_by_id(transaction_id)
        if not old_transaction:
            return None
        
        stmt = update(Transaction).where(Transaction.id == transaction_id).values(**update_data)
        self.db.execute(stmt)
        
        # TODO: Пересчитать холдинги если изменились ключевые поля
        # Это сложная логика, требующая отката старых изменений и применения новых
        
        self.db.commit()
        return self.get_by_id(transaction_id)
    
    def delete(self, transaction_id: int) -> bool:
        """Удаление транзакции с пересчетом холдингов."""
        transaction = self.get_by_id(transaction_id)
        if not transaction:
            return False
        
        try:
            # TODO: Откатить изменения в холдингах
            # Это требует сложной логики отката FIFO операций
            
            stmt = delete(Transaction).where(Transaction.id == transaction_id)
            result = self.db.execute(stmt)
            self.db.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка удаления транзакции {transaction_id}: {e}")
            raise
    
    def get_portfolio_cashflows(
        self,
        portfolio_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Transaction]:
        """Получение денежных потоков портфеля (дивиденды, купоны)."""
        cashflow_types = [
            TransactionType.DIVIDEND,
            TransactionType.COUPON,
            TransactionType.DEPOSIT,
            TransactionType.WITHDRAWAL
        ]
        
        return self.get_portfolio_transactions(
            portfolio_id=portfolio_id,
            start_date=start_date,
            end_date=end_date,
            transaction_type=cashflow_types
        )
    
    def get_transaction_stats(
        self,
        account_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Получение статистики по транзакциям."""
        stmt = select(Transaction).where(Transaction.account_id == account_id)
        
        if start_date:
            stmt = stmt.where(Transaction.ts >= start_date)
        
        if end_date:
            stmt = stmt.where(Transaction.ts <= end_date)
        
        # Общее количество транзакций
        count_result = self.db.execute(
            select(func.count()).select_from(stmt.subquery())
        )
        total_count = count_result.scalar()
        
        # Статистика по типам
        type_stats_stmt = (
            stmt.add_columns(
                func.count().label('count'),
                func.sum(Transaction.gross).label('total_amount')
            )
            .group_by(Transaction.transaction_type)
        )
        
        type_stats_result = self.db.execute(type_stats_stmt)
        type_stats = {}
        
        for row in type_stats_result:
            transaction_type = row[0].transaction_type
            type_stats[transaction_type.value] = {
                'count': row.count,
                'total_amount': float(row.total_amount or 0)
            }
        
        return {
            'total_count': total_count,
            'by_type': type_stats,
            'period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            }
        }
    
    def deduplicate_by_hash(
        self,
        account_id: int,
        transaction_hash: str
    ) -> bool:
        """Проверка на дублирование транзакции по хешу."""
        # Предполагаем, что хеш хранится в поле meta как JSON
        stmt = select(func.count()).where(
            and_(
                Transaction.account_id == account_id,
                Transaction.meta.contains(f'"hash":"{transaction_hash}"')
            )
        )
        
        result = self.db.execute(stmt)
        count = result.scalar()
        
        return count > 0
