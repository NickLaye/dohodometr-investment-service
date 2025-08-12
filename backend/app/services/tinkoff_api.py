"""
Сервис интеграции с Tinkoff Invest API
Автоматическая синхронизация портфелей, сделок и позиций
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import httpx
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.user import User
from ..models.portfolio import Portfolio
from ..models.transaction import Transaction
from ..models.instrument import Instrument
from ..models.broker_connection import BrokerConnection

logger = logging.getLogger(__name__)


@dataclass
class TinkoffCredentials:
    """Учетные данные для подключения к Tinkoff API"""
    token: str
    sandbox: bool = False


@dataclass
class TinkoffPosition:
    """Позиция в портфеле Tинькофф"""
    figi: str
    ticker: str
    name: str
    quantity: Decimal
    avg_price: Decimal
    current_price: Decimal
    currency: str
    expected_yield: Decimal


@dataclass
class TinkoffOperation:
    """Операция из истории Тинькофф"""
    id: str
    date: datetime
    operation_type: str
    figi: str
    ticker: str
    quantity: int
    price: Decimal
    payment: Decimal
    currency: str
    commission: Optional[Decimal] = None


class TinkoffAPIClient:
    """Клиент для работы с Tinkoff Invest API"""
    
    BASE_URL = "https://invest-public-api.tinkoff.ru/rest"
    SANDBOX_URL = "https://invest-public-api.tinkoff.ru/rest/tinkoff.public.invest.api.contract.v1.SandboxService"
    
    def __init__(self, credentials: TinkoffCredentials):
        self.token = credentials.token
        self.sandbox = credentials.sandbox
        self.base_url = self.SANDBOX_URL if credentials.sandbox else self.BASE_URL
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "x-app-name": "dohodometr.ru"
        }
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Выполнить HTTP запрос к API Тинькофф"""
        url = f"{self.base_url}/{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    timeout=30.0,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Tinkoff API error {e.response.status_code}: {e.response.text}")
                raise TinkoffAPIException(f"API error: {e.response.status_code}")
            except httpx.RequestError as e:
                logger.error(f"Tinkoff API request error: {e}")
                raise TinkoffAPIException(f"Request error: {e}")
    
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """Получить список счетов пользователя"""
        data = await self._make_request("POST", "GetAccounts", json={})
        return data.get("accounts", [])
    
    async def get_portfolio(self, account_id: str) -> List[TinkoffPosition]:
        """Получить портфель по счету"""
        data = await self._make_request(
            "POST", 
            "GetPortfolio", 
            json={"accountId": account_id}
        )
        
        positions = []
        for pos in data.get("positions", []):
            if pos.get("figi"):
                positions.append(TinkoffPosition(
                    figi=pos["figi"],
                    ticker=pos.get("ticker", ""),
                    name=pos.get("name", ""),
                    quantity=Decimal(str(pos.get("quantity", 0))),
                    avg_price=self._quotation_to_decimal(pos.get("averagePositionPrice")),
                    current_price=self._quotation_to_decimal(pos.get("currentPrice")),
                    currency=pos.get("averagePositionPrice", {}).get("currency", "RUB"),
                    expected_yield=self._quotation_to_decimal(pos.get("expectedYield"))
                ))
        
        return positions
    
    async def get_operations(
        self, 
        account_id: str, 
        from_date: datetime, 
        to_date: datetime
    ) -> List[TinkoffOperation]:
        """Получить операции за период"""
        data = await self._make_request(
            "POST",
            "GetOperations",
            json={
                "accountId": account_id,
                "from": from_date.isoformat(),
                "to": to_date.isoformat()
            }
        )
        
        operations = []
        for op in data.get("operations", []):
            if op.get("figi") and op.get("state") == "OPERATION_STATE_EXECUTED":
                operations.append(TinkoffOperation(
                    id=op["id"],
                    date=datetime.fromisoformat(op["date"].replace("Z", "+00:00")),
                    operation_type=op["operationType"],
                    figi=op["figi"],
                    ticker=op.get("ticker", ""),
                    quantity=op.get("quantity", 0),
                    price=self._quotation_to_decimal(op.get("price")),
                    payment=self._quotation_to_decimal(op.get("payment")),
                    currency=op.get("currency", "RUB"),
                    commission=self._quotation_to_decimal(op.get("commission"))
                ))
        
        return operations
    
    async def get_instrument_by_figi(self, figi: str) -> Optional[Dict[str, Any]]:
        """Получить информацию об инструменте по FIGI"""
        try:
            data = await self._make_request(
                "POST",
                "GetInstrumentBy",
                json={
                    "idType": "INSTRUMENT_ID_TYPE_FIGI",
                    "id": figi
                }
            )
            return data.get("instrument")
        except Exception as e:
            logger.warning(f"Failed to get instrument {figi}: {e}")
            return None
    
    def _quotation_to_decimal(self, quotation: Optional[Dict[str, Any]]) -> Decimal:
        """Конвертировать Quotation в Decimal"""
        if not quotation:
            return Decimal("0")
        
        units = quotation.get("units", 0)
        nano = quotation.get("nano", 0)
        
        return Decimal(str(units)) + Decimal(str(nano)) / Decimal("1000000000")


class TinkoffSyncService:
    """Сервис синхронизации данных с Тинькофф"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def sync_user_portfolios(self, user_id: int, credentials: TinkoffCredentials) -> Dict[str, Any]:
        """Синхронизировать все портфели пользователя"""
        client = TinkoffAPIClient(credentials)
        
        try:
            # Получаем список счетов
            accounts = await client.get_accounts()
            
            results = {
                "success": True,
                "accounts_synced": 0,
                "positions_synced": 0,
                "operations_synced": 0,
                "errors": []
            }
            
            for account in accounts:
                try:
                    account_id = account["id"]
                    account_name = account.get("name", f"Счет {account_id}")
                    
                    # Создаем или обновляем подключение к брокеру
                    connection = await self._ensure_broker_connection(
                        user_id, account_id, account_name, credentials
                    )
                    
                    # Синхронизируем портфель
                    portfolio_result = await self._sync_portfolio(client, connection, account_id)
                    results["positions_synced"] += portfolio_result["positions_synced"]
                    
                    # Синхронизируем операции за последние 30 дней
                    operations_result = await self._sync_operations(client, connection, account_id)
                    results["operations_synced"] += operations_result["operations_synced"]
                    
                    results["accounts_synced"] += 1
                    
                except Exception as e:
                    error_msg = f"Error syncing account {account.get('id')}: {e}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            # Обновляем время последней синхронизации
            await self._update_last_sync_time(user_id)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to sync user {user_id} portfolios: {e}")
            return {
                "success": False,
                "error": str(e),
                "accounts_synced": 0,
                "positions_synced": 0,
                "operations_synced": 0
            }
    
    async def _ensure_broker_connection(
        self, 
        user_id: int, 
        account_id: str, 
        account_name: str, 
        credentials: TinkoffCredentials
    ) -> BrokerConnection:
        """Создать или обновить подключение к брокеру"""
        
        connection = self.db.query(BrokerConnection).filter(
            BrokerConnection.user_id == user_id,
            BrokerConnection.broker_name == "tinkoff",
            BrokerConnection.account_id == account_id
        ).first()
        
        if not connection:
            connection = BrokerConnection(
                user_id=user_id,
                broker_name="tinkoff",
                account_id=account_id,
                account_name=account_name,
                is_active=True,
                credentials_encrypted=self._encrypt_credentials(credentials),
                last_sync_at=datetime.utcnow()
            )
            self.db.add(connection)
        else:
            connection.account_name = account_name
            connection.is_active = True
            connection.last_sync_at = datetime.utcnow()
        
        self.db.commit()
        return connection
    
    async def _sync_portfolio(self, client: TinkoffAPIClient, connection: BrokerConnection, account_id: str) -> Dict[str, Any]:
        """Синхронизировать позиции портфеля"""
        positions = await client.get_portfolio(account_id)
        
        # Получаем или создаем портфель
        portfolio = self.db.query(Portfolio).filter(
            Portfolio.user_id == connection.user_id,
            Portfolio.broker_account_id == account_id
        ).first()
        
        if not portfolio:
            portfolio = Portfolio(
                user_id=connection.user_id,
                name=f"Тинькофф: {connection.account_name}",
                broker_name="tinkoff",
                broker_account_id=account_id,
                currency="RUB"
            )
            self.db.add(portfolio)
            self.db.commit()
        
        positions_synced = 0
        
        for position in positions:
            try:
                # Получаем или создаем инструмент
                instrument = await self._ensure_instrument(client, position.figi, position.ticker)
                
                # Обновляем текущую позицию
                # Здесь должна быть логика обновления позиций в портфеле
                # TODO: Реализовать модель Position
                
                positions_synced += 1
                
            except Exception as e:
                logger.error(f"Failed to sync position {position.ticker}: {e}")
        
        return {"positions_synced": positions_synced}
    
    async def _sync_operations(self, client: TinkoffAPIClient, connection: BrokerConnection, account_id: str) -> Dict[str, Any]:
        """Синхронизировать операции"""
        # Синхронизируем операции за последние 30 дней
        to_date = datetime.utcnow()
        from_date = to_date - timedelta(days=30)
        
        operations = await client.get_operations(account_id, from_date, to_date)
        operations_synced = 0
        
        for operation in operations:
            try:
                # Проверяем, не существует ли уже такая операция
                existing = self.db.query(Transaction).filter(
                    Transaction.external_id == operation.id
                ).first()
                
                if existing:
                    continue
                
                # Получаем инструмент
                instrument = await self._ensure_instrument(client, operation.figi, operation.ticker)
                
                # Создаем транзакцию
                transaction = Transaction(
                    portfolio_id=None,  # TODO: Связать с портфелем
                    instrument_id=instrument.id if instrument else None,
                    transaction_type=self._map_operation_type(operation.operation_type),
                    quantity=Decimal(str(operation.quantity)),
                    price=operation.price,
                    total_amount=operation.payment,
                    commission=operation.commission or Decimal("0"),
                    currency=operation.currency,
                    executed_at=operation.date,
                    external_id=operation.id,
                    broker_name="tinkoff"
                )
                
                self.db.add(transaction)
                operations_synced += 1
                
            except Exception as e:
                logger.error(f"Failed to sync operation {operation.id}: {e}")
        
        if operations_synced > 0:
            self.db.commit()
        
        return {"operations_synced": operations_synced}
    
    async def _ensure_instrument(self, client: TinkoffAPIClient, figi: str, ticker: str) -> Optional[Instrument]:
        """Получить или создать инструмент"""
        instrument = self.db.query(Instrument).filter(
            Instrument.figi == figi
        ).first()
        
        if instrument:
            return instrument
        
        # Получаем данные об инструменте из API
        instrument_data = await client.get_instrument_by_figi(figi)
        
        if not instrument_data:
            return None
        
        instrument = Instrument(
            figi=figi,
            ticker=ticker,
            isin=instrument_data.get("isin"),
            name=instrument_data.get("name", ticker),
            instrument_type=self._map_instrument_type(instrument_data.get("instrumentType")),
            currency=instrument_data.get("currency", "RUB"),
            exchange=instrument_data.get("exchange"),
            country_of_risk=instrument_data.get("countryOfRisk"),
            sector=instrument_data.get("sector"),
            lot_size=instrument_data.get("lot", 1),
            min_price_increment=Decimal(str(instrument_data.get("minPriceIncrement", 0.01))),
            is_trading_available=True
        )
        
        self.db.add(instrument)
        self.db.commit()
        
        return instrument
    
    def _map_operation_type(self, tinkoff_type: str) -> str:
        """Маппинг типов операций Тинькофф в наши типы"""
        mapping = {
            "OPERATION_TYPE_BUY": "BUY",
            "OPERATION_TYPE_SELL": "SELL",
            "OPERATION_TYPE_DIVIDEND": "DIVIDEND",
            "OPERATION_TYPE_COUPON": "COUPON",
            "OPERATION_TYPE_BROKER_FEE": "FEE",
            "OPERATION_TYPE_SUCCESS_FEE": "FEE",
            "OPERATION_TYPE_MARGIN_FEE": "FEE",
            "OPERATION_TYPE_BUY_CARD": "BUY",
            "OPERATION_TYPE_SELL_CARD": "SELL"
        }
        return mapping.get(tinkoff_type, "OTHER")
    
    def _map_instrument_type(self, tinkoff_type: str) -> str:
        """Маппинг типов инструментов"""
        mapping = {
            "share": "STOCK",
            "bond": "BOND",
            "etf": "ETF",
            "currency": "CURRENCY",
            "future": "FUTURE",
            "option": "OPTION"
        }
        return mapping.get(tinkoff_type, "OTHER")
    
    def _encrypt_credentials(self, credentials: TinkoffCredentials) -> str:
        """Зашифровать учетные данные для хранения"""
        # TODO: Реализовать шифрование токена
        return credentials.token
    
    async def _update_last_sync_time(self, user_id: int):
        """Обновить время последней синхронизации"""
        connections = self.db.query(BrokerConnection).filter(
            BrokerConnection.user_id == user_id,
            BrokerConnection.broker_name == "tinkoff"
        ).all()
        
        for connection in connections:
            connection.last_sync_at = datetime.utcnow()
        
        self.db.commit()


class TinkoffAPIException(Exception):
    """Исключение при работе с Tinkoff API"""
    pass


# Автоматическая синхронизация в фоне
class TinkoffAutoSyncService:
    """Сервис автоматической синхронизации в фоне"""
    
    def __init__(self, db: Session):
        self.db = db
        self.sync_service = TinkoffSyncService(db)
    
    async def sync_all_active_connections(self):
        """Синхронизировать все активные подключения"""
        connections = self.db.query(BrokerConnection).filter(
            BrokerConnection.broker_name == "tinkoff",
            BrokerConnection.is_active == True
        ).all()
        
        logger.info(f"Starting auto-sync for {len(connections)} Tinkoff connections")
        
        for connection in connections:
            try:
                credentials = TinkoffCredentials(
                    token=connection.credentials_encrypted,  # TODO: Расшифровать
                    sandbox=False
                )
                
                result = await self.sync_service.sync_user_portfolios(
                    connection.user_id, 
                    credentials
                )
                
                if result["success"]:
                    logger.info(f"Auto-sync completed for user {connection.user_id}")
                else:
                    logger.error(f"Auto-sync failed for user {connection.user_id}: {result.get('error')}")
                    
            except Exception as e:
                logger.error(f"Auto-sync error for connection {connection.id}: {e}")
        
        logger.info("Auto-sync completed for all connections")


# Celery задача для периодической синхронизации
async def run_tinkoff_auto_sync():
    """Задача для автоматической синхронизации Тинькофф"""
    from ..core.database import SessionLocal
    
    db = SessionLocal()
    try:
        service = TinkoffAutoSyncService(db)
        await service.sync_all_active_connections()
    finally:
        db.close()
