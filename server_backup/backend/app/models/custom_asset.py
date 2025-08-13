"""
Модели для произвольных активов (недвижимость, вклады, бизнес и др.)
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any

from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text, Boolean, Date, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
import uuid

from ..core.database import Base


class CustomAssetType(str, Enum):
    """Типы произвольных активов"""
    REAL_ESTATE = "real_estate"          # Недвижимость
    DEPOSIT = "deposit"                   # Банковские вклады
    BUSINESS = "business"                 # Доли в бизнесе
    P2P_LENDING = "p2p_lending"          # P2P кредитование
    PRECIOUS_METALS = "precious_metals"   # Драгоценные металлы
    ART_COLLECTIBLES = "art_collectibles" # Искусство и коллекции
    STRUCTURED_PRODUCTS = "structured_products" # Структурные продукты
    ALTERNATIVE = "alternative"           # Альтернативные инвестиции
    OTHER = "other"                      # Прочие


class CustomAssetSubtype(str, Enum):
    """Подтипы произвольных активов"""
    # Недвижимость
    APARTMENT = "apartment"              # Квартира
    HOUSE = "house"                     # Дом
    COMMERCIAL = "commercial"           # Коммерческая недвижимость
    LAND = "land"                      # Земельный участок
    GARAGE = "garage"                  # Гараж
    
    # Вклады
    SAVINGS_ACCOUNT = "savings_account" # Сберегательный счет
    TERM_DEPOSIT = "term_deposit"      # Срочный вклад
    
    # Драгоценные металлы
    GOLD = "gold"                      # Золото
    SILVER = "silver"                  # Серебро
    PLATINUM = "platinum"              # Платина
    PALLADIUM = "palladium"           # Палладий


class ValuationMethod(str, Enum):
    """Методы оценки стоимости"""
    MANUAL = "manual"                   # Ручная оценка
    MARKET_PRICE = "market_price"      # Рыночная цена
    APPRAISAL = "appraisal"           # Оценка экспертом
    COST_METHOD = "cost_method"        # Затратный метод
    INCOME_METHOD = "income_method"    # Доходный метод
    COMPARABLE_SALES = "comparable_sales" # Метод сравнительных продаж


class CustomAsset(Base):
    """Произвольный актив"""
    __tablename__ = "custom_assets"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Базовая информация
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    asset_type = Column(ENUM(CustomAssetType), nullable=False)
    subtype = Column(ENUM(CustomAssetSubtype))
    
    # Финансовые параметры
    currency = Column(String(3), default="RUB")
    purchase_date = Column(Date)
    purchase_price = Column(Numeric(15, 2))
    current_value = Column(Numeric(15, 2))
    valuation_date = Column(Date)
    valuation_method = Column(ENUM(ValuationMethod), default=ValuationMethod.MANUAL)
    
    # Количество/доля
    quantity = Column(Numeric(15, 6), default=1.0)  # Например, доля в бизнесе
    unit_type = Column(String(50))  # м², кв.м, доли, кг и т.д.
    
    # Доходность
    annual_income = Column(Numeric(15, 2), default=0)  # Годовой доход (аренда, дивиденды)
    income_frequency = Column(String(20))  # monthly, quarterly, annually
    last_income_date = Column(Date)
    
    # Расходы
    annual_expenses = Column(Numeric(15, 2), default=0)  # Годовые расходы (налоги, обслуживание)
    
    # Дополнительные данные (JSON)
    asset_metadata = Column(JSON)  # Адрес, характеристики, документы и т.д.
    
    # Флаги
    is_income_generating = Column(Boolean, default=False)
    is_liquid = Column(Boolean, default=False)  # Ликвидность
    is_active = Column(Boolean, default=True)
    
    # Аудит
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    portfolio = relationship("Portfolio", back_populates="custom_assets")
    transactions = relationship("CustomAssetTransaction", back_populates="asset")
    valuations = relationship("CustomAssetValuation", back_populates="asset")
    
    @hybrid_property
    def current_yield(self) -> Optional[Decimal]:
        """Текущая доходность"""
        if not self.current_value or self.current_value == 0:
            return None
        return (self.annual_income or Decimal(0)) / self.current_value * 100
    
    @hybrid_property
    def total_return(self) -> Optional[Decimal]:
        """Общая доходность с момента покупки"""
        if not self.purchase_price or self.purchase_price == 0:
            return None
        if not self.current_value:
            return None
        
        capital_gain = self.current_value - self.purchase_price
        total_income = self._calculate_total_income()
        
        return (capital_gain + total_income) / self.purchase_price * 100
    
    def _calculate_total_income(self) -> Decimal:
        """Рассчитать общий доход за время владения"""
        if not self.purchase_date or not self.annual_income:
            return Decimal(0)
        
        years_owned = (date.today() - self.purchase_date).days / 365.25
        return self.annual_income * Decimal(str(years_owned))
    
    def get_market_value(self) -> Decimal:
        """Получить рыночную стоимость"""
        return self.current_value or Decimal(0)
    
    def update_valuation(self, new_value: Decimal, method: ValuationMethod = ValuationMethod.MANUAL):
        """Обновить оценку стоимости"""
        self.current_value = new_value
        self.valuation_date = date.today()
        self.valuation_method = method
        self.updated_at = datetime.utcnow()


class CustomAssetTransaction(Base):
    """Транзакции по произвольным активам"""
    __tablename__ = "custom_asset_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    asset_id = Column(Integer, ForeignKey("custom_assets.id"), nullable=False)
    
    # Тип транзакции
    transaction_type = Column(String(50), nullable=False)  # income, expense, purchase, sale, valuation
    
    # Финансовые данные
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="RUB")
    
    # Описание
    description = Column(String(500))
    category = Column(String(100))  # rent, maintenance, tax, insurance и т.д.
    
    # Даты
    transaction_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Документы и метаданные
    document_url = Column(String(500))
    asset_metadata = Column(JSON)
    
    # Связи
    asset = relationship("CustomAsset", back_populates="transactions")


class CustomAssetValuation(Base):
    """История оценок произвольных активов"""
    __tablename__ = "custom_asset_valuations"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("custom_assets.id"), nullable=False)
    
    # Оценка
    value = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="RUB")
    valuation_date = Column(Date, nullable=False)
    method = Column(ENUM(ValuationMethod), nullable=False)
    
    # Источник оценки
    valuator = Column(String(200))  # Кто проводил оценку
    source = Column(String(200))    # Источник данных
    confidence_level = Column(Integer)  # Уровень уверенности в оценке (1-100)
    
    # Дополнительная информация
    notes = Column(Text)
    document_url = Column(String(500))
    asset_metadata = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    asset = relationship("CustomAsset", back_populates="valuations")


# Специализированные модели для разных типов активов

class RealEstateAsset(Base):
    """Недвижимость - расширенная модель"""
    __tablename__ = "real_estate_assets"
    
    id = Column(Integer, primary_key=True, index=True)
    custom_asset_id = Column(Integer, ForeignKey("custom_assets.id"), nullable=False)
    
    # Адрес и местоположение
    country = Column(String(2), default="RU")
    region = Column(String(100))
    city = Column(String(100))
    address = Column(String(500))
    postal_code = Column(String(20))
    
    # Координаты
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    
    # Характеристики
    total_area = Column(Numeric(10, 2))  # Общая площадь
    living_area = Column(Numeric(10, 2)) # Жилая площадь
    land_area = Column(Numeric(10, 2))   # Площадь участка
    rooms_count = Column(Integer)
    floor = Column(Integer)
    total_floors = Column(Integer)
    
    # Год постройки и состояние
    construction_year = Column(Integer)
    renovation_year = Column(Integer)
    condition = Column(String(50))  # excellent, good, fair, poor
    
    # Правовая информация
    ownership_type = Column(String(50))  # full, shared, leasehold
    ownership_share = Column(Numeric(5, 4), default=1.0)  # Доля в собственности
    cadastral_number = Column(String(50))
    
    # Аренда
    is_rented = Column(Boolean, default=False)
    rental_income_monthly = Column(Numeric(10, 2))
    rental_yield = Column(Numeric(5, 2))  # Рентабельность в %
    
    # Расходы
    property_tax_annual = Column(Numeric(10, 2))
    maintenance_annual = Column(Numeric(10, 2))
    insurance_annual = Column(Numeric(10, 2))
    utilities_monthly = Column(Numeric(10, 2))
    
    # Связи
    custom_asset = relationship("CustomAsset")


class DepositAsset(Base):
    """Банковские вклады"""
    __tablename__ = "deposit_assets"
    
    id = Column(Integer, primary_key=True, index=True)
    custom_asset_id = Column(Integer, ForeignKey("custom_assets.id"), nullable=False)
    
    # Банк и продукт
    bank_name = Column(String(200), nullable=False)
    product_name = Column(String(200))
    account_number = Column(String(50))
    
    # Условия вклада
    deposit_type = Column(String(50))  # savings, term, compound
    interest_rate = Column(Numeric(5, 4), nullable=False)  # Процентная ставка
    capitalization = Column(Boolean, default=False)  # Капитализация процентов
    
    # Сроки
    opening_date = Column(Date, nullable=False)
    maturity_date = Column(Date)  # Дата окончания для срочных вкладов
    auto_renewal = Column(Boolean, default=False)
    
    # Суммы
    initial_amount = Column(Numeric(15, 2), nullable=False)
    current_balance = Column(Numeric(15, 2), nullable=False)
    accrued_interest = Column(Numeric(15, 2), default=0)
    
    # Условия пополнения и снятия
    can_replenish = Column(Boolean, default=False)
    can_withdraw = Column(Boolean, default=False)
    min_balance = Column(Numeric(15, 2))
    penalty_rate = Column(Numeric(5, 4))  # Штраф за досрочное снятие
    
    # Страхование
    is_insured = Column(Boolean, default=True)
    insurance_amount = Column(Numeric(15, 2))  # Сумма страхового покрытия
    
    # Связи
    custom_asset = relationship("CustomAsset")
    
    @hybrid_property
    def days_to_maturity(self) -> Optional[int]:
        """Дней до погашения"""
        if not self.maturity_date:
            return None
        return (self.maturity_date - date.today()).days
    
    @hybrid_property
    def effective_yield(self) -> Decimal:
        """Эффективная доходность с учетом капитализации"""
        if self.capitalization:
            # Сложный процент
            return (1 + self.interest_rate / 12) ** 12 - 1
        else:
            # Простой процент
            return self.interest_rate


class BusinessAsset(Base):
    """Доли в бизнесе"""
    __tablename__ = "business_assets"
    
    id = Column(Integer, primary_key=True, index=True)
    custom_asset_id = Column(Integer, ForeignKey("custom_assets.id"), nullable=False)
    
    # Информация о компании
    company_name = Column(String(200), nullable=False)
    legal_name = Column(String(200))
    inn = Column(String(12))
    industry = Column(String(100))
    business_model = Column(String(100))
    
    # Доля в бизнесе
    ownership_percentage = Column(Numeric(5, 4), nullable=False)  # Доля в %
    number_of_shares = Column(Integer)
    total_shares = Column(Integer)
    
    # Финансовые показатели
    last_valuation = Column(Numeric(15, 2))
    revenue_annual = Column(Numeric(15, 2))
    profit_annual = Column(Numeric(15, 2))
    ebitda = Column(Numeric(15, 2))
    
    # Дивиденды и выплаты
    dividend_yield = Column(Numeric(5, 4))
    last_dividend_date = Column(Date)
    last_dividend_amount = Column(Numeric(15, 2))
    
    # Права и ограничения
    voting_rights = Column(Boolean, default=True)
    board_seat = Column(Boolean, default=False)
    liquidation_preference = Column(Boolean, default=False)
    
    # Связи
    custom_asset = relationship("CustomAsset")
