"""
Интеграция с Binance API для учета криптовалютных активов.

Поддерживаемые функции:
- Получение балансов кошельков
- История торговых операций
- Стейкинг и Earn продукты
- Futures и Margin операции
- DeFi и NFT активы
- Конвертация криптовалют в фиат
"""

import hashlib
import hmac
import time
import logging
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import aiohttp
import asyncio

logger = logging.getLogger(__name__)


class BinanceProductType(Enum):
    """Типы продуктов Binance"""
    SPOT = "spot"                    # Спот торговля
    FUTURES = "futures"              # Фьючерсы
    MARGIN = "margin"                # Маржинальная торговля
    SAVINGS = "savings"              # Binance Earn
    STAKING = "staking"              # Стейкинг
    MINING = "mining"                # Майнинг
    NFT = "nft"                      # NFT
    DEFI = "defi"                    # DeFi стейкинг


class OrderType(Enum):
    """Типы ордеров"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"
    TAKE_PROFIT = "TAKE_PROFIT"
    TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"


class OrderSide(Enum):
    """Сторона сделки"""
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class CryptoBalance:
    """Баланс криптовалюты"""
    asset: str
    free: Decimal                    # Доступно
    locked: Decimal                  # Заблокировано
    total: Decimal                   # Общий баланс
    usd_value: Optional[Decimal] = None  # Стоимость в USD
    rub_value: Optional[Decimal] = None  # Стоимость в RUB


@dataclass
class CryptoTransaction:
    """Криптовалютная транзакция"""
    transaction_id: str
    symbol: str                      # Например BTC/USDT
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Decimal
    quote_qty: Decimal              # Количество в котируемой валюте
    commission: Decimal
    commission_asset: str
    timestamp: datetime
    is_maker: bool                  # Мейкер или тейкер
    product_type: BinanceProductType = BinanceProductType.SPOT


@dataclass
class StakingReward:
    """Награда за стейкинг"""
    asset: str
    amount: Decimal
    timestamp: datetime
    product_name: str
    apy: Optional[Decimal] = None


@dataclass
class CryptoPortfolioSnapshot:
    """Снимок криптопортфеля"""
    timestamp: datetime
    total_value_usd: Decimal
    total_value_rub: Decimal
    balances: List[CryptoBalance]
    staking_rewards: List[StakingReward]
    daily_pnl: Decimal
    total_pnl: Decimal


class BinanceAPIError(Exception):
    """Ошибка при работе с Binance API"""
    pass


class BinanceAPIClient:
    """
    Клиент для работы с Binance API
    
    Поддерживает:
    - Spot, Futures, Margin API
    - Binance Earn (стейкинг, сбережения)
    - Конвертация валют
    - Исторические данные
    """
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        """
        Инициализация клиента
        
        Args:
            api_key: API ключ Binance
            api_secret: Секретный ключ Binance
            testnet: Использовать тестовую сеть
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # Базовые URL
        if testnet:
            self.base_url = "https://testnet.binance.vision"
            self.futures_base_url = "https://testnet.binancefuture.com"
        else:
            self.base_url = "https://api.binance.com"
            self.futures_base_url = "https://fapi.binance.com"
            
        # Лимиты запросов
        self.request_weight = 0
        self.last_request_time = 0
        self.max_requests_per_minute = 1200
        
        # Кеширование курсов
        self._price_cache = {}
        self._cache_expiry = {}
        self.cache_ttl = 60  # секунд

    def _generate_signature(self, query_string: str) -> str:
        """Генерация подписи для авторизованных запросов"""
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def _get_timestamp(self) -> int:
        """Получить текущий timestamp для API"""
        return int(time.time() * 1000)

    async def _make_request(self,
                          method: str,
                          endpoint: str,
                          params: Optional[Dict] = None,
                          signed: bool = False,
                          futures: bool = False) -> Dict:
        """
        Выполнить HTTP запрос к API
        
        Args:
            method: HTTP метод
            endpoint: Эндпоинт API
            params: Параметры запроса
            signed: Требуется подпись
            futures: Использовать Futures API
            
        Returns:
            Ответ API в виде словаря
        """
        if params is None:
            params = {}
            
        # Выбор базового URL
        base_url = self.futures_base_url if futures else self.base_url
        url = f"{base_url}{endpoint}"
        
        # Заголовки
        headers = {"X-MBX-APIKEY": self.api_key}
        
        # Добавление timestamp для подписанных запросов
        if signed:
            params['timestamp'] = self._get_timestamp()
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            params['signature'] = self._generate_signature(query_string)
        
        # Контроль лимитов
        await self._check_rate_limits()
        
        try:
            async with aiohttp.ClientSession() as session:
                if method.upper() == 'GET':
                    async with session.get(url, params=params, headers=headers) as response:
                        data = await response.json()
                elif method.upper() == 'POST':
                    async with session.post(url, data=params, headers=headers) as response:
                        data = await response.json()
                else:
                    raise ValueError(f"Неподдерживаемый HTTP метод: {method}")
                
                # Проверка на ошибки API
                if 'code' in data and data['code'] != 200:
                    raise BinanceAPIError(f"Binance API Error: {data.get('msg', 'Unknown error')}")
                
                return data
                
        except aiohttp.ClientError as e:
            logger.error(f"HTTP ошибка при запросе к Binance API: {e}")
            raise BinanceAPIError(f"Ошибка соединения: {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при запросе к Binance API: {e}")
            raise BinanceAPIError(f"Неожиданная ошибка: {e}")

    async def _check_rate_limits(self):
        """Проверка и соблюдение лимитов запросов"""
        current_time = time.time()
        
        # Простая реализация rate limiting
        if current_time - self.last_request_time < 1:  # Максимум 1 запрос в секунду
            await asyncio.sleep(1 - (current_time - self.last_request_time))
        
        self.last_request_time = time.time()

    async def get_account_info(self) -> Dict:
        """Получить информацию об аккаунте"""
        return await self._make_request('GET', '/api/v3/account', signed=True)

    async def get_spot_balances(self) -> List[CryptoBalance]:
        """
        Получить спот балансы
        
        Returns:
            Список балансов криптовалют
        """
        account_info = await self.get_account_info()
        balances = []
        
        for balance_data in account_info.get('balances', []):
            free = Decimal(balance_data['free'])
            locked = Decimal(balance_data['locked'])
            total = free + locked
            
            # Фильтруем нулевые балансы
            if total > 0:
                balance = CryptoBalance(
                    asset=balance_data['asset'],
                    free=free,
                    locked=locked,
                    total=total
                )
                balances.append(balance)
        
        # Добавляем USD и RUB стоимость
        await self._enrich_balances_with_prices(balances)
        
        return balances

    async def get_futures_balances(self) -> List[CryptoBalance]:
        """Получить фьючерсные балансы"""
        try:
            account_info = await self._make_request(
                'GET', '/fapi/v2/account', signed=True, futures=True
            )
            
            balances = []
            for balance_data in account_info.get('assets', []):
                wallet_balance = Decimal(balance_data['walletBalance'])
                
                if wallet_balance > 0:
                    balance = CryptoBalance(
                        asset=balance_data['asset'],
                        free=wallet_balance,
                        locked=Decimal('0'),
                        total=wallet_balance
                    )
                    balances.append(balance)
            
            await self._enrich_balances_with_prices(balances)
            return balances
            
        except BinanceAPIError:
            logger.warning("Не удалось получить фьючерсные балансы")
            return []

    async def _enrich_balances_with_prices(self, balances: List[CryptoBalance]):
        """Обогатить балансы актуальными ценами"""
        for balance in balances:
            if balance.asset == 'USDT':
                balance.usd_value = balance.total
                balance.rub_value = balance.total * await self.get_usd_rub_rate()
            elif balance.asset == 'BUSD':
                balance.usd_value = balance.total
                balance.rub_value = balance.total * await self.get_usd_rub_rate()
            else:
                # Получаем цену в USDT
                usd_price = await self.get_asset_price_usd(balance.asset)
                if usd_price:
                    balance.usd_value = balance.total * usd_price
                    balance.rub_value = balance.usd_value * await self.get_usd_rub_rate()

    async def get_asset_price_usd(self, asset: str) -> Optional[Decimal]:
        """
        Получить цену актива в USD
        
        Args:
            asset: Символ актива (например, BTC)
            
        Returns:
            Цена в USD или None если не найдена
        """
        # Проверяем кеш
        cache_key = f"{asset}_USD"
        if (cache_key in self._price_cache and 
            time.time() < self._cache_expiry.get(cache_key, 0)):
            return self._price_cache[cache_key]
        
        try:
            # Пробуем разные пары
            symbols_to_try = [f"{asset}USDT", f"{asset}BUSD", f"{asset}USD"]
            
            for symbol in symbols_to_try:
                try:
                    response = await self._make_request(
                        'GET', '/api/v3/ticker/price', {'symbol': symbol}
                    )
                    price = Decimal(response['price'])
                    
                    # Кешируем результат
                    self._price_cache[cache_key] = price
                    self._cache_expiry[cache_key] = time.time() + self.cache_ttl
                    
                    return price
                except BinanceAPIError:
                    continue
            
            logger.warning(f"Не удалось найти цену для {asset}")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при получении цены {asset}: {e}")
            return None

    async def get_usd_rub_rate(self) -> Decimal:
        """Получить курс USD/RUB"""
        # В реальной реализации можно использовать ЦБ РФ API
        # Для демонстрации используем фиксированный курс
        return Decimal('75.0')

    async def get_trading_history(self,
                                symbol: Optional[str] = None,
                                start_time: Optional[datetime] = None,
                                end_time: Optional[datetime] = None,
                                limit: int = 500) -> List[CryptoTransaction]:
        """
        Получить историю торгов
        
        Args:
            symbol: Торговая пара (например, BTCUSDT)
            start_time: Начальное время
            end_time: Конечное время
            limit: Максимум записей
            
        Returns:
            Список транзакций
        """
        params = {'limit': min(limit, 1000)}
        
        if start_time:
            params['startTime'] = int(start_time.timestamp() * 1000)
        if end_time:
            params['endTime'] = int(end_time.timestamp() * 1000)
        if symbol:
            params['symbol'] = symbol
        
        try:
            # Получаем все сделки
            trades = await self._make_request('GET', '/api/v3/myTrades', params, signed=True)
            
            transactions = []
            for trade in trades:
                transaction = CryptoTransaction(
                    transaction_id=str(trade['id']),
                    symbol=trade['symbol'],
                    side=OrderSide.BUY if trade['isBuyer'] else OrderSide.SELL,
                    order_type=OrderType.MARKET,  # Упрощение
                    quantity=Decimal(trade['qty']),
                    price=Decimal(trade['price']),
                    quote_qty=Decimal(trade['quoteQty']),
                    commission=Decimal(trade['commission']),
                    commission_asset=trade['commissionAsset'],
                    timestamp=datetime.fromtimestamp(trade['time'] / 1000),
                    is_maker=trade['isMaker'],
                    product_type=BinanceProductType.SPOT
                )
                transactions.append(transaction)
            
            return sorted(transactions, key=lambda x: x.timestamp)
            
        except BinanceAPIError as e:
            logger.error(f"Ошибка при получении истории торгов: {e}")
            return []

    async def get_staking_history(self,
                                product: Optional[str] = None,
                                start_time: Optional[datetime] = None,
                                end_time: Optional[datetime] = None) -> List[StakingReward]:
        """
        Получить историю стейкинга и Earn продуктов
        
        Args:
            product: Название продукта
            start_time: Начальное время
            end_time: Конечное время
            
        Returns:
            Список наград за стейкинг
        """
        params = {}
        if product:
            params['product'] = product
        if start_time:
            params['startTime'] = int(start_time.timestamp() * 1000)
        if end_time:
            params['endTime'] = int(end_time.timestamp() * 1000)
        
        try:
            # Пробуем получить данные через разные эндпоинты
            rewards = []
            
            # Staking rewards
            try:
                staking_data = await self._make_request(
                    'GET', '/sapi/v1/staking/stakingRecord', params, signed=True
                )
                
                for record in staking_data:
                    reward = StakingReward(
                        asset=record['asset'],
                        amount=Decimal(record['amount']),
                        timestamp=datetime.fromtimestamp(record['time'] / 1000),
                        product_name=record.get('product', 'Staking'),
                        apy=Decimal(record.get('apy', 0)) if record.get('apy') else None
                    )
                    rewards.append(reward)
            except BinanceAPIError:
                logger.info("Staking записи недоступны")
            
            # Savings rewards
            try:
                savings_params = params.copy()
                savings_params['lendingType'] = 'DAILY'
                
                savings_data = await self._make_request(
                    'GET', '/sapi/v1/lending/union/redemptionRecord', 
                    savings_params, signed=True
                )
                
                for record in savings_data:
                    reward = StakingReward(
                        asset=record['asset'],
                        amount=Decimal(record['amount']),
                        timestamp=datetime.fromtimestamp(record['createTime'] / 1000),
                        product_name=record.get('productName', 'Savings')
                    )
                    rewards.append(reward)
            except BinanceAPIError:
                logger.info("Savings записи недоступны")
            
            return sorted(rewards, key=lambda x: x.timestamp)
            
        except Exception as e:
            logger.error(f"Ошибка при получении истории стейкинга: {e}")
            return []

    async def get_portfolio_snapshot(self) -> CryptoPortfolioSnapshot:
        """
        Получить снимок криптопортфеля
        
        Returns:
            Полный снимок портфеля со всеми данными
        """
        # Получаем все балансы
        spot_balances = await self.get_spot_balances()
        futures_balances = await self.get_futures_balances()
        
        all_balances = spot_balances + futures_balances
        
        # Объединяем одинаковые активы
        consolidated_balances = {}
        for balance in all_balances:
            if balance.asset in consolidated_balances:
                existing = consolidated_balances[balance.asset]
                existing.total += balance.total
                existing.free += balance.free
                existing.locked += balance.locked
                if balance.usd_value:
                    existing.usd_value = (existing.usd_value or Decimal('0')) + balance.usd_value
                if balance.rub_value:
                    existing.rub_value = (existing.rub_value or Decimal('0')) + balance.rub_value
            else:
                consolidated_balances[balance.asset] = balance
        
        final_balances = list(consolidated_balances.values())
        
        # Рассчитываем общую стоимость
        total_usd = sum(b.usd_value or Decimal('0') for b in final_balances)
        total_rub = sum(b.rub_value or Decimal('0') for b in final_balances)
        
        # Получаем награды за стейкинг за последние 30 дней
        thirty_days_ago = datetime.now() - timedelta(days=30)
        staking_rewards = await self.get_staking_history(
            start_time=thirty_days_ago
        )
        
        # Упрощенный расчет PnL (нужна более сложная логика)
        daily_pnl = Decimal('0')  # Заглушка
        total_pnl = Decimal('0')  # Заглушка
        
        return CryptoPortfolioSnapshot(
            timestamp=datetime.now(),
            total_value_usd=total_usd,
            total_value_rub=total_rub,
            balances=final_balances,
            staking_rewards=staking_rewards,
            daily_pnl=daily_pnl,
            total_pnl=total_pnl
        )

    async def calculate_crypto_taxes_rf(self, 
                                      transactions: List[CryptoTransaction],
                                      tax_year: int) -> Dict[str, Decimal]:
        """
        Рассчитать налоги с криптовалютных операций для РФ
        
        Args:
            transactions: Список транзакций
            tax_year: Налоговый год
            
        Returns:
            Словарь с налоговыми расчетами
        """
        year_transactions = [
            t for t in transactions 
            if t.timestamp.year == tax_year
        ]
        
        # Группируем операции по парам
        pairs_pnl = {}
        
        for tx in year_transactions:
            base_asset = tx.symbol.replace('USDT', '').replace('BUSD', '').replace('BTC', '')
            
            if base_asset not in pairs_pnl:
                pairs_pnl[base_asset] = {
                    'trades': [],
                    'total_pnl_usd': Decimal('0'),
                    'total_pnl_rub': Decimal('0')
                }
            
            pairs_pnl[base_asset]['trades'].append(tx)
        
        # Рассчитываем PnL для каждой пары (упрощенный FIFO)
        total_taxable_income_rub = Decimal('0')
        
        for asset, data in pairs_pnl.items():
            # Упрощенный расчет - нужна более сложная логика FIFO
            buys = [t for t in data['trades'] if t.side == OrderSide.BUY]
            sells = [t for t in data['trades'] if t.side == OrderSide.SELL]
            
            total_buy_value = sum(t.quote_qty for t in buys)
            total_sell_value = sum(t.quote_qty for t in sells)
            
            pnl_usd = total_sell_value - total_buy_value
            pnl_rub = pnl_usd * await self.get_usd_rub_rate()
            
            data['total_pnl_usd'] = pnl_usd
            data['total_pnl_rub'] = pnl_rub
            
            if pnl_rub > 0:  # Только положительный результат облагается налогом
                total_taxable_income_rub += pnl_rub
        
        # Применяем ставку НДФЛ 13%
        ndfl_amount = total_taxable_income_rub * Decimal('0.13')
        
        return {
            'total_taxable_income_rub': total_taxable_income_rub,
            'ndfl_amount': ndfl_amount,
            'ndfl_rate': Decimal('0.13'),
            'pairs_pnl': pairs_pnl,
            'tax_year': tax_year
        }


class CryptoPortfolioService:
    """Сервис для работы с криптопортфелем"""
    
    def __init__(self, binance_client: BinanceAPIClient):
        self.binance_client = binance_client
    
    async def sync_portfolio(self, user_id: str) -> CryptoPortfolioSnapshot:
        """
        Синхронизировать криптопортфель пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Обновленный снимок портфеля
        """
        try:
            snapshot = await self.binance_client.get_portfolio_snapshot()
            
            # Здесь бы сохранили в базу данных
            logger.info(f"Портфель пользователя {user_id} синхронизирован")
            logger.info(f"Общая стоимость: ${snapshot.total_value_usd:,.2f}")
            
            return snapshot
            
        except BinanceAPIError as e:
            logger.error(f"Ошибка синхронизации портфеля {user_id}: {e}")
            raise
    
    async def get_crypto_allocation(self, 
                                  snapshot: CryptoPortfolioSnapshot) -> Dict[str, Decimal]:
        """
        Получить распределение активов в портфеле
        
        Args:
            snapshot: Снимок портфеля
            
        Returns:
            Словарь с процентным распределением
        """
        if snapshot.total_value_usd == 0:
            return {}
        
        allocation = {}
        for balance in snapshot.balances:
            if balance.usd_value and balance.usd_value > 0:
                percentage = (balance.usd_value / snapshot.total_value_usd) * 100
                allocation[balance.asset] = percentage.quantize(Decimal('0.01'))
        
        return allocation
    
    async def generate_crypto_report(self, 
                                   snapshot: CryptoPortfolioSnapshot,
                                   transactions: List[CryptoTransaction],
                                   tax_year: int = None) -> str:
        """
        Генерировать отчет по криптопортфелю
        
        Args:
            snapshot: Снимок портфеля
            transactions: История транзакций
            tax_year: Налоговый год
            
        Returns:
            Текстовый отчет
        """
        if tax_year is None:
            tax_year = datetime.now().year
        
        allocation = await self.get_crypto_allocation(snapshot)
        tax_data = await self.binance_client.calculate_crypto_taxes_rf(
            transactions, tax_year
        )
        
        report = f"""
ОТЧЕТ ПО КРИПТОПОРТФЕЛЮ
Дата: {snapshot.timestamp.strftime('%d.%m.%Y %H:%M')}

ОБЩАЯ СТОИМОСТЬ:
💰 USD: ${snapshot.total_value_usd:,.2f}
💰 RUB: {snapshot.total_value_rub:,.2f} руб

АКТИВЫ ({len(snapshot.balances)} позиций):
"""
        
        for balance in sorted(snapshot.balances, 
                            key=lambda x: x.usd_value or Decimal('0'), 
                            reverse=True):
            if balance.total > 0:
                percentage = allocation.get(balance.asset, Decimal('0'))
                report += f"  {balance.asset}: {balance.total:.8f} "
                report += f"(${balance.usd_value or 0:,.2f}, {percentage:.1f}%)\n"
        
        if snapshot.staking_rewards:
            report += f"\nСТЕЙКИНГ НАГРАДЫ (последние 30 дней):\n"
            staking_by_asset = {}
            for reward in snapshot.staking_rewards:
                if reward.asset not in staking_by_asset:
                    staking_by_asset[reward.asset] = Decimal('0')
                staking_by_asset[reward.asset] += reward.amount
            
            for asset, amount in staking_by_asset.items():
                report += f"  {asset}: {amount:.8f}\n"
        
        report += f"""
НАЛОГОВЫЕ ОБЯЗАТЕЛЬСТВА ({tax_year} год):
📊 Налогооблагаемый доход: {tax_data['total_taxable_income_rub']:,.2f} руб
💸 НДФЛ к доплате: {tax_data['ndfl_amount']:,.2f} руб
📈 Эффективная ставка: {tax_data['ndfl_rate']:.1%}

РЕКОМЕНДАЦИИ:
• Ведите детальный учет всех операций с криптовалютой
• Учитывайте курсовые разности при конвертации в рубли
• Подавайте декларацию при доходе свыше 5 млн руб/год
• Рассмотрите возможность налогового планирования
        """
        
        return report.strip()
