"""
Сервис для работы с произвольными активами
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ..models.custom_asset import (
    CustomAsset, CustomAssetType, CustomAssetSubtype, ValuationMethod,
    CustomAssetTransaction, CustomAssetValuation,
    RealEstateAsset, DepositAsset, BusinessAsset
)
from ..models.portfolio import Portfolio


@dataclass
class CustomAssetCreateRequest:
    """Запрос на создание произвольного актива"""
    portfolio_id: int
    name: str
    asset_type: CustomAssetType
    subtype: Optional[CustomAssetSubtype] = None
    description: Optional[str] = None
    currency: str = "RUB"
    purchase_date: Optional[date] = None
    purchase_price: Optional[Decimal] = None
    current_value: Optional[Decimal] = None
    quantity: Decimal = Decimal("1.0")
    unit_type: Optional[str] = None
    annual_income: Decimal = Decimal("0")
    annual_expenses: Decimal = Decimal("0")
    is_income_generating: bool = False
    is_liquid: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RealEstateCreateRequest:
    """Запрос на создание недвижимости"""
    custom_asset: CustomAssetCreateRequest
    country: str = "RU"
    region: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    total_area: Optional[Decimal] = None
    living_area: Optional[Decimal] = None
    rooms_count: Optional[int] = None
    floor: Optional[int] = None
    construction_year: Optional[int] = None
    condition: Optional[str] = None
    ownership_type: str = "full"
    ownership_share: Decimal = Decimal("1.0")
    is_rented: bool = False
    rental_income_monthly: Optional[Decimal] = None


@dataclass
class DepositCreateRequest:
    """Запрос на создание банковского вклада"""
    custom_asset: CustomAssetCreateRequest
    bank_name: str
    product_name: Optional[str] = None
    interest_rate: Decimal
    deposit_type: str = "term"
    capitalization: bool = False
    opening_date: date
    maturity_date: Optional[date] = None
    initial_amount: Decimal
    current_balance: Decimal
    can_replenish: bool = False
    can_withdraw: bool = False
    is_insured: bool = True
    insurance_amount: Optional[Decimal] = None


class CustomAssetsService:
    """Сервис для работы с произвольными активами"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_custom_asset(self, request: CustomAssetCreateRequest) -> CustomAsset:
        """Создать произвольный актив"""
        # Проверяем существование портфеля
        portfolio = self.db.query(Portfolio).filter(Portfolio.id == request.portfolio_id).first()
        if not portfolio:
            raise ValueError(f"Portfolio {request.portfolio_id} not found")
        
        asset = CustomAsset(
            portfolio_id=request.portfolio_id,
            name=request.name,
            description=request.description,
            asset_type=request.asset_type,
            subtype=request.subtype,
            currency=request.currency,
            purchase_date=request.purchase_date,
            purchase_price=request.purchase_price,
            current_value=request.current_value or request.purchase_price,
            valuation_date=date.today() if request.current_value else None,
            quantity=request.quantity,
            unit_type=request.unit_type,
            annual_income=request.annual_income,
            annual_expenses=request.annual_expenses,
            is_income_generating=request.is_income_generating,
            is_liquid=request.is_liquid,
            metadata=request.metadata or {}
        )
        
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        
        return asset
    
    def create_real_estate(self, request: RealEstateCreateRequest) -> CustomAsset:
        """Создать недвижимость"""
        # Создаем базовый актив
        asset = self.create_custom_asset(request.custom_asset)
        
        # Создаем расширенную информацию о недвижимости
        real_estate = RealEstateAsset(
            custom_asset_id=asset.id,
            country=request.country,
            region=request.region,
            city=request.city,
            address=request.address,
            total_area=request.total_area,
            living_area=request.living_area,
            rooms_count=request.rooms_count,
            floor=request.floor,
            construction_year=request.construction_year,
            condition=request.condition,
            ownership_type=request.ownership_type,
            ownership_share=request.ownership_share,
            is_rented=request.is_rented,
            rental_income_monthly=request.rental_income_monthly
        )
        
        self.db.add(real_estate)
        self.db.commit()
        
        return asset
    
    def create_deposit(self, request: DepositCreateRequest) -> CustomAsset:
        """Создать банковский вклад"""
        # Создаем базовый актив
        asset = self.create_custom_asset(request.custom_asset)
        
        # Создаем расширенную информацию о вкладе
        deposit = DepositAsset(
            custom_asset_id=asset.id,
            bank_name=request.bank_name,
            product_name=request.product_name,
            interest_rate=request.interest_rate,
            deposit_type=request.deposit_type,
            capitalization=request.capitalization,
            opening_date=request.opening_date,
            maturity_date=request.maturity_date,
            initial_amount=request.initial_amount,
            current_balance=request.current_balance,
            can_replenish=request.can_replenish,
            can_withdraw=request.can_withdraw,
            is_insured=request.is_insured,
            insurance_amount=request.insurance_amount
        )
        
        self.db.add(deposit)
        self.db.commit()
        
        return asset
    
    def update_asset_valuation(
        self, 
        asset_id: int, 
        new_value: Decimal, 
        method: ValuationMethod = ValuationMethod.MANUAL,
        notes: Optional[str] = None
    ) -> CustomAsset:
        """Обновить оценку стоимости актива"""
        asset = self.db.query(CustomAsset).filter(CustomAsset.id == asset_id).first()
        if not asset:
            raise ValueError(f"Asset {asset_id} not found")
        
        # Создаем запись в истории оценок
        valuation = CustomAssetValuation(
            asset_id=asset_id,
            value=new_value,
            currency=asset.currency,
            valuation_date=date.today(),
            method=method,
            notes=notes
        )
        self.db.add(valuation)
        
        # Обновляем текущую стоимость
        asset.update_valuation(new_value, method)
        
        self.db.commit()
        return asset
    
    def add_transaction(
        self,
        asset_id: int,
        transaction_type: str,
        amount: Decimal,
        transaction_date: date,
        description: Optional[str] = None,
        category: Optional[str] = None
    ) -> CustomAssetTransaction:
        """Добавить транзакцию по активу"""
        transaction = CustomAssetTransaction(
            asset_id=asset_id,
            transaction_type=transaction_type,
            amount=amount,
            transaction_date=transaction_date,
            description=description,
            category=category
        )
        
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        
        return transaction
    
    def get_portfolio_custom_assets(self, portfolio_id: int) -> List[CustomAsset]:
        """Получить все произвольные активы портфеля"""
        return self.db.query(CustomAsset).filter(
            and_(
                CustomAsset.portfolio_id == portfolio_id,
                CustomAsset.is_active == True
            )
        ).all()
    
    def get_asset_with_details(self, asset_id: int) -> Optional[Dict[str, Any]]:
        """Получить актив с детальной информацией"""
        asset = self.db.query(CustomAsset).filter(CustomAsset.id == asset_id).first()
        if not asset:
            return None
        
        result = {
            "asset": asset,
            "transactions": asset.transactions,
            "valuations": asset.valuations
        }
        
        # Добавляем специфичную информацию по типу актива
        if asset.asset_type == CustomAssetType.REAL_ESTATE:
            real_estate = self.db.query(RealEstateAsset).filter(
                RealEstateAsset.custom_asset_id == asset_id
            ).first()
            result["real_estate_details"] = real_estate
            
        elif asset.asset_type == CustomAssetType.DEPOSIT:
            deposit = self.db.query(DepositAsset).filter(
                DepositAsset.custom_asset_id == asset_id
            ).first()
            result["deposit_details"] = deposit
            
        elif asset.asset_type == CustomAssetType.BUSINESS:
            business = self.db.query(BusinessAsset).filter(
                BusinessAsset.custom_asset_id == asset_id
            ).first()
            result["business_details"] = business
        
        return result
    
    def calculate_portfolio_custom_assets_value(self, portfolio_id: int) -> Dict[str, Any]:
        """Рассчитать общую стоимость произвольных активов в портфеле"""
        assets = self.get_portfolio_custom_assets(portfolio_id)
        
        total_value = Decimal("0")
        total_annual_income = Decimal("0")
        total_annual_expenses = Decimal("0")
        
        by_type = {}
        by_currency = {}
        
        for asset in assets:
            if asset.current_value:
                total_value += asset.current_value
                
                # По типам
                if asset.asset_type.value not in by_type:
                    by_type[asset.asset_type.value] = {"value": Decimal("0"), "count": 0}
                by_type[asset.asset_type.value]["value"] += asset.current_value
                by_type[asset.asset_type.value]["count"] += 1
                
                # По валютам
                if asset.currency not in by_currency:
                    by_currency[asset.currency] = Decimal("0")
                by_currency[asset.currency] += asset.current_value
            
            if asset.annual_income:
                total_annual_income += asset.annual_income
            
            if asset.annual_expenses:
                total_annual_expenses += asset.annual_expenses
        
        return {
            "total_value": total_value,
            "total_annual_income": total_annual_income,
            "total_annual_expenses": total_annual_expenses,
            "net_annual_income": total_annual_income - total_annual_expenses,
            "assets_count": len(assets),
            "by_type": by_type,
            "by_currency": by_currency,
            "yield_on_cost": (total_annual_income - total_annual_expenses) / total_value * 100 if total_value > 0 else 0
        }
    
    def get_income_generating_assets(self, portfolio_id: int) -> List[Dict[str, Any]]:
        """Получить активы, генерирующие доход"""
        assets = self.db.query(CustomAsset).filter(
            and_(
                CustomAsset.portfolio_id == portfolio_id,
                CustomAsset.is_income_generating == True,
                CustomAsset.is_active == True
            )
        ).all()
        
        result = []
        for asset in assets:
            asset_data = {
                "asset": asset,
                "monthly_income": asset.annual_income / 12 if asset.annual_income else 0,
                "monthly_expenses": asset.annual_expenses / 12 if asset.annual_expenses else 0,
                "net_monthly_income": (asset.annual_income - asset.annual_expenses) / 12 if asset.annual_income or asset.annual_expenses else 0,
                "yield_percent": asset.current_yield
            }
            
            # Добавляем информацию о следующих поступлениях
            if asset.asset_type == CustomAssetType.DEPOSIT:
                deposit_details = self.db.query(DepositAsset).filter(
                    DepositAsset.custom_asset_id == asset.id
                ).first()
                if deposit_details:
                    asset_data["next_payment_date"] = deposit_details.maturity_date
                    asset_data["interest_rate"] = deposit_details.interest_rate
            
            result.append(asset_data)
        
        return result
    
    def update_deposit_balance(self, asset_id: int, new_balance: Decimal, accrued_interest: Decimal = None):
        """Обновить баланс вклада"""
        deposit = self.db.query(DepositAsset).filter(
            DepositAsset.custom_asset_id == asset_id
        ).first()
        
        if not deposit:
            raise ValueError(f"Deposit asset {asset_id} not found")
        
        deposit.current_balance = new_balance
        if accrued_interest is not None:
            deposit.accrued_interest = accrued_interest
        
        # Обновляем также общую стоимость актива
        asset = self.db.query(CustomAsset).filter(CustomAsset.id == asset_id).first()
        if asset:
            asset.current_value = new_balance
            asset.valuation_date = date.today()
            asset.updated_at = datetime.utcnow()
        
        self.db.commit()
    
    def get_assets_by_type(self, portfolio_id: int, asset_type: CustomAssetType) -> List[CustomAsset]:
        """Получить активы определенного типа"""
        return self.db.query(CustomAsset).filter(
            and_(
                CustomAsset.portfolio_id == portfolio_id,
                CustomAsset.asset_type == asset_type,
                CustomAsset.is_active == True
            )
        ).all()
    
    def calculate_real_estate_analytics(self, portfolio_id: int) -> Dict[str, Any]:
        """Аналитика по недвижимости"""
        real_estate_assets = self.get_assets_by_type(portfolio_id, CustomAssetType.REAL_ESTATE)
        
        if not real_estate_assets:
            return {"total_value": 0, "assets": []}
        
        total_value = sum(asset.current_value or 0 for asset in real_estate_assets)
        total_rental_income = Decimal("0")
        total_area = Decimal("0")
        
        by_city = {}
        by_type = {}
        
        for asset in real_estate_assets:
            # Получаем детали недвижимости
            details = self.db.query(RealEstateAsset).filter(
                RealEstateAsset.custom_asset_id == asset.id
            ).first()
            
            if details:
                if details.rental_income_monthly:
                    total_rental_income += details.rental_income_monthly * 12
                
                if details.total_area:
                    total_area += details.total_area
                
                # По городам
                city = details.city or "Не указан"
                if city not in by_city:
                    by_city[city] = {"value": Decimal("0"), "count": 0}
                by_city[city]["value"] += asset.current_value or 0
                by_city[city]["count"] += 1
                
                # По подтипам
                subtype = asset.subtype.value if asset.subtype else "other"
                if subtype not in by_type:
                    by_type[subtype] = {"value": Decimal("0"), "count": 0}
                by_type[subtype]["value"] += asset.current_value or 0
                by_type[subtype]["count"] += 1
        
        return {
            "total_value": total_value,
            "total_rental_income": total_rental_income,
            "average_price_per_sqm": total_value / total_area if total_area > 0 else 0,
            "rental_yield": total_rental_income / total_value * 100 if total_value > 0 else 0,
            "assets_count": len(real_estate_assets),
            "by_city": by_city,
            "by_type": by_type
        }
    
    def delete_asset(self, asset_id: int, user_id: int) -> bool:
        """Удалить актив (мягкое удаление)"""
        asset = self.db.query(CustomAsset).filter(CustomAsset.id == asset_id).first()
        
        if not asset:
            return False
        
        # Проверяем права доступа
        if asset.portfolio.user_id != user_id:
            raise ValueError("Access denied")
        
        asset.is_active = False
        asset.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
