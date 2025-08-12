"""
Модели для хранения данных о криптовалютных активах.

Поддерживает:
- Спот торговлю
- Фьючерсы и маржинальную торговлю
- Стейкинг и Earn продукты
- DeFi операции
- NFT коллекции
"""

from sqlalchemy import Column, String, Numeric, DateTime, Boolean, Integer, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class CryptoPlatform(enum.Enum):
    """Криптовалютные платформы"""
    BINANCE = "binance"
    BYBIT = "bybit"
    OKEX = "okex"
    HUOBI = "huobi"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    KUCOIN = "kucoin"
    METAMASK = "metamask"
    TRUST_WALLET = "trust_wallet"
    LEDGER = "ledger"
    TREZOR = "trezor"


class CryptoAssetType(enum.Enum):
    """Типы криптоактивов"""
    CRYPTOCURRENCY = "cryptocurrency"  # Обычная криптовалюта
    STABLECOIN = "stablecoin"          # Стейблкоин
    DEFI_TOKEN = "defi_token"          # DeFi токен
    NFT = "nft"                        # NFT
    WRAPPED_TOKEN = "wrapped_token"     # Обернутый токен
    GOVERNANCE_TOKEN = "governance_token"  # Токен управления
    UTILITY_TOKEN = "utility_token"    # Утилитарный токен


class CryptoProductType(enum.Enum):
    """Типы криптопродуктов"""
    SPOT = "spot"                    # Спот торговля
    FUTURES = "futures"              # Фьючерсы
    MARGIN = "margin"                # Маржинальная торговля
    SAVINGS = "savings"              # Накопительные продукты
    STAKING = "staking"              # Стейкинг
    MINING = "mining"                # Майнинг
    DEFI_FARMING = "defi_farming"    # DeFi фарминг
    LIQUIDITY_POOL = "liquidity_pool" # Пулы ликвидности


class CryptoExchange(Base):
    """Криптовалютная биржа"""
    __tablename__ = "crypto_exchanges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    platform = Column(Enum(CryptoPlatform), nullable=False)
    api_key_encrypted = Column(Text)  # Зашифрованный API ключ
    api_secret_encrypted = Column(Text)  # Зашифрованный секрет
    is_testnet = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="crypto_exchanges")
    accounts = relationship("CryptoAccount", back_populates="exchange")
    transactions = relationship("CryptoTransaction", back_populates="exchange")


class CryptoAsset(Base):
    """Криптовалютный актив"""
    __tablename__ = "crypto_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False, index=True)  # BTC, ETH, etc.
    name = Column(String(100), nullable=False)  # Bitcoin, Ethereum
    asset_type = Column(Enum(CryptoAssetType), nullable=False)
    
    # Технические характеристики
    blockchain = Column(String(50))  # Bitcoin, Ethereum, BSC
    contract_address = Column(String(100))  # Для токенов
    decimals = Column(Integer, default=18)
    
    # Рыночные данные
    current_price_usd = Column(Numeric(20, 8))
    market_cap = Column(Numeric(20, 2))
    volume_24h = Column(Numeric(20, 2))
    price_change_24h = Column(Numeric(10, 4))
    
    # Метаданные
    description = Column(Text)
    website_url = Column(String(255))
    whitepaper_url = Column(String(255))
    logo_url = Column(String(255))
    
    # Системные поля
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    balances = relationship("CryptoBalance", back_populates="asset")
    transactions = relationship("CryptoTransaction", back_populates="asset")
    price_history = relationship("CryptoPriceHistory", back_populates="asset")


class CryptoAccount(Base):
    """Криптовалютный счет"""
    __tablename__ = "crypto_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_name = Column(String(100), nullable=False)
    account_type = Column(Enum(CryptoProductType), nullable=False)
    exchange_id = Column(UUID(as_uuid=True), ForeignKey("crypto_exchanges.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Адреса кошельков (для внешних кошельков)
    wallet_addresses = Column(JSONB)  # {"BTC": "1A1zP1...", "ETH": "0x..."}
    
    # Статистика
    total_value_usd = Column(Numeric(20, 2), default=0)
    total_value_rub = Column(Numeric(20, 2), default=0)
    daily_pnl = Column(Numeric(20, 2), default=0)
    total_pnl = Column(Numeric(20, 2), default=0)
    
    # Настройки
    is_active = Column(Boolean, default=True)
    auto_sync = Column(Boolean, default=True)
    sync_interval_hours = Column(Integer, default=1)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_sync = Column(DateTime)
    
    # Связи
    exchange = relationship("CryptoExchange", back_populates="accounts")
    user = relationship("User", back_populates="crypto_accounts")
    balances = relationship("CryptoBalance", back_populates="account")
    transactions = relationship("CryptoTransaction", back_populates="account")


class CryptoBalance(Base):
    """Баланс криптовалюты"""
    __tablename__ = "crypto_balances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crypto_accounts.id"), nullable=False)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("crypto_assets.id"), nullable=False)
    
    # Балансы
    free_amount = Column(Numeric(20, 8), nullable=False, default=0)  # Доступно
    locked_amount = Column(Numeric(20, 8), nullable=False, default=0)  # Заблокировано
    staked_amount = Column(Numeric(20, 8), nullable=False, default=0)  # В стейкинге
    total_amount = Column(Numeric(20, 8), nullable=False, default=0)  # Общий баланс
    
    # Стоимость
    avg_purchase_price = Column(Numeric(20, 8))  # Средняя цена покупки
    current_price_usd = Column(Numeric(20, 8))
    current_value_usd = Column(Numeric(20, 2))
    current_value_rub = Column(Numeric(20, 2))
    
    # PnL
    unrealized_pnl_usd = Column(Numeric(20, 2))
    unrealized_pnl_rub = Column(Numeric(20, 2))
    unrealized_pnl_percent = Column(Numeric(10, 4))
    
    # Метаданные
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    account = relationship("CryptoAccount", back_populates="balances")
    asset = relationship("CryptoAsset", back_populates="balances")


class CryptoTransaction(Base):
    """Криптовалютная транзакция"""
    __tablename__ = "crypto_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(100))  # ID транзакции на бирже
    account_id = Column(UUID(as_uuid=True), ForeignKey("crypto_accounts.id"), nullable=False)
    exchange_id = Column(UUID(as_uuid=True), ForeignKey("crypto_exchanges.id"), nullable=False)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("crypto_assets.id"), nullable=False)
    
    # Основные параметры
    transaction_type = Column(String(20), nullable=False)  # BUY, SELL, DEPOSIT, WITHDRAWAL, REWARD
    side = Column(String(10))  # BUY/SELL для торговых операций
    symbol = Column(String(20), nullable=False)  # BTCUSDT, ETHUSDT
    
    # Количества и цены
    quantity = Column(Numeric(20, 8), nullable=False)
    price = Column(Numeric(20, 8))
    quote_quantity = Column(Numeric(20, 8))  # Количество в котируемой валюте
    
    # Комиссии
    commission = Column(Numeric(20, 8), default=0)
    commission_asset = Column(String(10))
    
    # Дополнительная информация
    order_type = Column(String(20))  # MARKET, LIMIT, STOP_LOSS
    is_maker = Column(Boolean)  # Мейкер или тейкер
    product_type = Column(Enum(CryptoProductType), nullable=False)
    
    # Временные метки
    executed_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Налоговые данные
    tax_lot_method = Column(String(10), default="FIFO")
    realized_pnl_usd = Column(Numeric(20, 2))
    realized_pnl_rub = Column(Numeric(20, 2))
    
    # Дополнительные данные (JSON)
    metadata = Column(JSONB)
    
    # Связи
    account = relationship("CryptoAccount", back_populates="transactions")
    exchange = relationship("CryptoExchange", back_populates="transactions")
    asset = relationship("CryptoAsset", back_populates="transactions")


class CryptoStakingReward(Base):
    """Награды за стейкинг"""
    __tablename__ = "crypto_staking_rewards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crypto_accounts.id"), nullable=False)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("crypto_assets.id"), nullable=False)
    
    # Детали награды
    amount = Column(Numeric(20, 8), nullable=False)
    product_name = Column(String(100), nullable=False)  # "BTC Savings", "ETH 2.0 Staking"
    apy = Column(Numeric(10, 4))  # Годовая доходность в процентах
    
    # Стоимость на момент получения
    price_usd_at_time = Column(Numeric(20, 8))
    value_usd_at_time = Column(Numeric(20, 2))
    value_rub_at_time = Column(Numeric(20, 2))
    
    # Временные метки
    rewarded_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Налоговые данные
    is_taxable = Column(Boolean, default=True)
    tax_category = Column(String(50), default="staking_reward")
    
    # Связи
    account = relationship("CryptoAccount")
    asset = relationship("CryptoAsset")


class CryptoPriceHistory(Base):
    """История цен криптовалют"""
    __tablename__ = "crypto_price_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("crypto_assets.id"), nullable=False)
    
    # Цены
    price_usd = Column(Numeric(20, 8), nullable=False)
    price_rub = Column(Numeric(20, 8))
    volume_24h = Column(Numeric(20, 2))
    market_cap = Column(Numeric(20, 2))
    
    # Изменения
    price_change_1h = Column(Numeric(10, 4))
    price_change_24h = Column(Numeric(10, 4))
    price_change_7d = Column(Numeric(10, 4))
    
    # Временная метка
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    asset = relationship("CryptoAsset", back_populates="price_history")


class CryptoNFT(Base):
    """NFT коллекция и токены"""
    __tablename__ = "crypto_nfts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crypto_accounts.id"), nullable=False)
    
    # Основная информация
    token_id = Column(String(100), nullable=False)
    contract_address = Column(String(100), nullable=False)
    blockchain = Column(String(50), nullable=False, default="ethereum")
    
    # Метаданные NFT
    name = Column(String(200))
    description = Column(Text)
    image_url = Column(String(500))
    animation_url = Column(String(500))
    
    # Коллекция
    collection_name = Column(String(200))
    collection_slug = Column(String(100))
    
    # Стоимость и характеристики
    purchase_price_eth = Column(Numeric(20, 8))
    purchase_price_usd = Column(Numeric(20, 2))
    current_floor_price = Column(Numeric(20, 8))
    estimated_value_usd = Column(Numeric(20, 2))
    
    # Редкость и характеристики
    rarity_rank = Column(Integer)
    rarity_score = Column(Numeric(10, 4))
    traits = Column(JSONB)  # JSON с атрибутами NFT
    
    # Временные метки
    purchased_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    account = relationship("CryptoAccount")


class CryptoDeFiPosition(Base):
    """DeFi позиции (пулы ликвидности, фарминг)"""
    __tablename__ = "crypto_defi_positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crypto_accounts.id"), nullable=False)
    
    # Протокол и пул
    protocol_name = Column(String(100), nullable=False)  # Uniswap, PancakeSwap, etc.
    pool_name = Column(String(100), nullable=False)      # ETH/USDC, BNB/BUSD
    pool_address = Column(String(100))
    blockchain = Column(String(50), nullable=False)
    
    # Позиция
    position_type = Column(String(50), nullable=False)   # liquidity_pool, yield_farming, lending
    lp_token_amount = Column(Numeric(20, 8))
    
    # Активы в пуле
    token0_symbol = Column(String(20))
    token0_amount = Column(Numeric(20, 8))
    token1_symbol = Column(String(20))
    token1_amount = Column(Numeric(20, 8))
    
    # Доходность
    apy = Column(Numeric(10, 4))
    rewards_earned = Column(JSONB)  # {"CAKE": 15.5, "BNB": 0.1}
    
    # Стоимость
    total_value_usd = Column(Numeric(20, 2))
    total_value_rub = Column(Numeric(20, 2))
    
    # Временные метки
    entered_at = Column(DateTime, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    account = relationship("CryptoAccount")


# Индексы для оптимизации запросов
from sqlalchemy import Index

# Индексы для быстрого поиска транзакций
Index('ix_crypto_transactions_account_date', 
      CryptoTransaction.account_id, CryptoTransaction.executed_at)
Index('ix_crypto_transactions_symbol_date', 
      CryptoTransaction.symbol, CryptoTransaction.executed_at)

# Индексы для балансов
Index('ix_crypto_balances_account_asset', 
      CryptoBalance.account_id, CryptoBalance.asset_id)

# Индексы для истории цен
Index('ix_crypto_price_history_asset_time', 
      CryptoPriceHistory.asset_id, CryptoPriceHistory.timestamp)
