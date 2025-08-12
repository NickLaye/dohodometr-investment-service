"""
Сервис ребалансировки портфелей
Умные рекомендации по оптимизации распределения активов
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ..models.portfolio import Portfolio
from ..models.instrument import Instrument
from ..models.transaction import Transaction
from ..models.custom_asset import CustomAsset
from ..services.portfolio_service import PortfolioService


class RebalancingStrategy(str, Enum):
    """Стратегии ребалансировки"""
    THRESHOLD = "threshold"          # По превышению порога
    CALENDAR = "calendar"            # По календарному графику
    MOMENTUM = "momentum"            # С учетом трендов
    CONSERVATIVE = "conservative"     # Консервативная
    AGGRESSIVE = "aggressive"        # Агрессивная


class RebalancingAction(str, Enum):
    """Действия при ребалансировке"""
    BUY = "buy"                     # Покупка
    SELL = "sell"                   # Продажа
    HOLD = "hold"                   # Удерживать


@dataclass
class TargetAllocation:
    """Целевое распределение актива"""
    instrument_id: Optional[int] = None
    custom_asset_id: Optional[int] = None
    asset_class: Optional[str] = None
    sector: Optional[str] = None
    currency: Optional[str] = None
    target_percent: Decimal = Decimal("0")
    min_percent: Optional[Decimal] = None
    max_percent: Optional[Decimal] = None


@dataclass
class CurrentHolding:
    """Текущая позиция"""
    instrument_id: Optional[int] = None
    custom_asset_id: Optional[int] = None
    symbol: str = ""
    name: str = ""
    current_value: Decimal = Decimal("0")
    current_percent: Decimal = Decimal("0")
    shares: Decimal = Decimal("0")
    avg_price: Decimal = Decimal("0")
    current_price: Decimal = Decimal("0")
    currency: str = "RUB"
    asset_class: Optional[str] = None
    sector: Optional[str] = None


@dataclass
class RebalancingRecommendation:
    """Рекомендация по ребалансировке"""
    instrument_id: Optional[int] = None
    custom_asset_id: Optional[int] = None
    symbol: str = ""
    name: str = ""
    action: RebalancingAction = RebalancingAction.HOLD
    current_percent: Decimal = Decimal("0")
    target_percent: Decimal = Decimal("0")
    deviation: Decimal = Decimal("0")
    amount_to_trade: Decimal = Decimal("0")
    shares_to_trade: Decimal = Decimal("0")
    priority: int = 0  # 1-10, где 10 - самый высокий приоритет
    reason: str = ""
    estimated_commission: Decimal = Decimal("0")
    tax_impact: Decimal = Decimal("0")


@dataclass
class RebalancingPlan:
    """План ребалансировки"""
    portfolio_id: int
    strategy: RebalancingStrategy
    total_value: Decimal
    cash_available: Decimal
    recommendations: List[RebalancingRecommendation]
    total_commission: Decimal
    total_tax_impact: Decimal
    expected_improvement: Decimal
    risk_metrics: Dict[str, Any]
    created_at: datetime


class RebalancingService:
    """Сервис ребалансировки портфелей"""
    
    def __init__(self, db: Session):
        self.db = db
        self.portfolio_service = PortfolioService(db)
    
    def create_rebalancing_plan(
        self,
        portfolio_id: int,
        target_allocations: List[TargetAllocation],
        strategy: RebalancingStrategy = RebalancingStrategy.THRESHOLD,
        threshold_percent: Decimal = Decimal("5"),
        max_trades: int = 10,
        available_cash: Decimal = Decimal("0")
    ) -> RebalancingPlan:
        """Создать план ребалансировки"""
        
        # Получаем текущие позиции
        current_holdings = self._get_current_holdings(portfolio_id)
        total_value = sum(holding.current_value for holding in current_holdings) + available_cash
        
        if total_value == 0:
            raise ValueError("Portfolio has zero value")
        
        # Рассчитываем текущие проценты
        for holding in current_holdings:
            holding.current_percent = holding.current_value / total_value * 100
        
        # Генерируем рекомендации
        recommendations = self._generate_recommendations(
            current_holdings,
            target_allocations,
            total_value,
            available_cash,
            strategy,
            threshold_percent,
            max_trades
        )
        
        # Рассчитываем общие метрики
        total_commission = sum(rec.estimated_commission for rec in recommendations)
        total_tax_impact = sum(rec.tax_impact for rec in recommendations)
        
        # Оценка улучшения
        expected_improvement = self._calculate_expected_improvement(
            current_holdings, recommendations, target_allocations
        )
        
        # Риск-метрики
        risk_metrics = self._calculate_risk_metrics(recommendations)
        
        return RebalancingPlan(
            portfolio_id=portfolio_id,
            strategy=strategy,
            total_value=total_value,
            cash_available=available_cash,
            recommendations=recommendations,
            total_commission=total_commission,
            total_tax_impact=total_tax_impact,
            expected_improvement=expected_improvement,
            risk_metrics=risk_metrics,
            created_at=datetime.utcnow()
        )
    
    def _get_current_holdings(self, portfolio_id: int) -> List[CurrentHolding]:
        """Получить текущие позиции портфеля"""
        holdings = []
        
        # Получаем позиции по обычным инструментам
        # TODO: Реализовать получение текущих позиций из модели Position
        # positions = self.db.query(Position).filter(Position.portfolio_id == portfolio_id).all()
        
        # Временная заглушка - получаем из транзакций
        transactions = self.db.query(Transaction).filter(
            Transaction.portfolio_id == portfolio_id
        ).all()
        
        # Группируем по инструментам
        positions_by_instrument = {}
        for tx in transactions:
            if tx.instrument_id not in positions_by_instrument:
                positions_by_instrument[tx.instrument_id] = {
                    "shares": Decimal("0"),
                    "total_cost": Decimal("0"),
                    "instrument": tx.instrument
                }
            
            if tx.transaction_type == "BUY":
                positions_by_instrument[tx.instrument_id]["shares"] += tx.quantity
                positions_by_instrument[tx.instrument_id]["total_cost"] += tx.total_amount
            elif tx.transaction_type == "SELL":
                positions_by_instrument[tx.instrument_id]["shares"] -= tx.quantity
                # TODO: Правильно рассчитать среднюю цену при продаже
        
        # Создаем CurrentHolding для каждой позиции
        for instrument_id, position_data in positions_by_instrument.items():
            if position_data["shares"] > 0:
                instrument = position_data["instrument"]
                avg_price = position_data["total_cost"] / position_data["shares"]
                current_price = self._get_current_price(instrument)
                current_value = position_data["shares"] * current_price
                
                holdings.append(CurrentHolding(
                    instrument_id=instrument_id,
                    symbol=instrument.ticker,
                    name=instrument.name,
                    current_value=current_value,
                    shares=position_data["shares"],
                    avg_price=avg_price,
                    current_price=current_price,
                    currency=instrument.currency,
                    asset_class=instrument.instrument_type,
                    sector=instrument.sector
                ))
        
        # Добавляем произвольные активы
        custom_assets = self.db.query(CustomAsset).filter(
            and_(
                CustomAsset.portfolio_id == portfolio_id,
                CustomAsset.is_active == True
            )
        ).all()
        
        for asset in custom_assets:
            if asset.current_value and asset.current_value > 0:
                holdings.append(CurrentHolding(
                    custom_asset_id=asset.id,
                    symbol=asset.name[:10],
                    name=asset.name,
                    current_value=asset.current_value,
                    currency=asset.currency,
                    asset_class=asset.asset_type.value,
                    shares=asset.quantity
                ))
        
        return holdings
    
    def _generate_recommendations(
        self,
        current_holdings: List[CurrentHolding],
        target_allocations: List[TargetAllocation],
        total_value: Decimal,
        available_cash: Decimal,
        strategy: RebalancingStrategy,
        threshold_percent: Decimal,
        max_trades: int
    ) -> List[RebalancingRecommendation]:
        """Генерировать рекомендации по ребалансировке"""
        
        recommendations = []
        
        # Создаем мапинг целевых распределений
        targets_by_instrument = {}
        targets_by_asset_class = {}
        
        for target in target_allocations:
            if target.instrument_id:
                targets_by_instrument[target.instrument_id] = target
            elif target.asset_class:
                targets_by_asset_class[target.asset_class] = target
        
        # Анализируем каждую позицию
        for holding in current_holdings:
            target = None
            
            # Ищем целевое распределение
            if holding.instrument_id and holding.instrument_id in targets_by_instrument:
                target = targets_by_instrument[holding.instrument_id]
            elif holding.asset_class and holding.asset_class in targets_by_asset_class:
                target = targets_by_asset_class[holding.asset_class]
            
            if not target:
                continue
            
            # Рассчитываем отклонение
            deviation = holding.current_percent - target.target_percent
            
            # Проверяем нужна ли корректировка
            if abs(deviation) > threshold_percent:
                
                if deviation > 0:
                    # Превышение - нужно продавать
                    action = RebalancingAction.SELL
                    target_value = total_value * target.target_percent / 100
                    amount_to_trade = holding.current_value - target_value
                    shares_to_trade = amount_to_trade / holding.current_price if holding.current_price > 0 else 0
                else:
                    # Недостаток - нужно покупать
                    action = RebalancingAction.BUY
                    target_value = total_value * target.target_percent / 100
                    amount_to_trade = target_value - holding.current_value
                    shares_to_trade = amount_to_trade / holding.current_price if holding.current_price > 0 else 0
                
                # Проверяем доступность средств для покупки
                if action == RebalancingAction.BUY and amount_to_trade > available_cash:
                    amount_to_trade = available_cash
                    shares_to_trade = amount_to_trade / holding.current_price if holding.current_price > 0 else 0
                
                # Рассчитываем приоритет
                priority = min(10, int(abs(deviation)))
                
                # Оценка комиссий и налогов
                estimated_commission = self._estimate_commission(amount_to_trade, holding.instrument_id)
                tax_impact = self._estimate_tax_impact(holding, amount_to_trade, action)
                
                recommendation = RebalancingRecommendation(
                    instrument_id=holding.instrument_id,
                    custom_asset_id=holding.custom_asset_id,
                    symbol=holding.symbol,
                    name=holding.name,
                    action=action,
                    current_percent=holding.current_percent,
                    target_percent=target.target_percent,
                    deviation=deviation,
                    amount_to_trade=amount_to_trade,
                    shares_to_trade=shares_to_trade,
                    priority=priority,
                    reason=f"Отклонение {deviation:.1f}% от целевого {target.target_percent:.1f}%",
                    estimated_commission=estimated_commission,
                    tax_impact=tax_impact
                )
                
                recommendations.append(recommendation)
        
        # Сортируем по приоритету и ограничиваем количество
        recommendations.sort(key=lambda x: x.priority, reverse=True)
        return recommendations[:max_trades]
    
    def _get_current_price(self, instrument: Instrument) -> Decimal:
        """Получить текущую цену инструмента"""
        # TODO: Интеграция с источниками котировок
        # Временная заглушка
        return Decimal("100.0")
    
    def _estimate_commission(self, amount: Decimal, instrument_id: Optional[int]) -> Decimal:
        """Оценить комиссию за сделку"""
        # Базовая комиссия 0.05%
        base_commission_rate = Decimal("0.0005")
        commission = amount * base_commission_rate
        
        # Минимальная комиссия 1 рубль
        return max(commission, Decimal("1.0"))
    
    def _estimate_tax_impact(
        self, 
        holding: CurrentHolding, 
        amount: Decimal, 
        action: RebalancingAction
    ) -> Decimal:
        """Оценить налоговое воздействие"""
        if action == RebalancingAction.SELL:
            # Рассчитываем потенциальную прибыль/убыток
            shares_to_sell = amount / holding.current_price if holding.current_price > 0 else 0
            profit = shares_to_sell * (holding.current_price - holding.avg_price)
            
            if profit > 0:
                # НДФЛ 13% с прибыли
                return profit * Decimal("0.13")
        
        return Decimal("0")
    
    def _calculate_expected_improvement(
        self,
        current_holdings: List[CurrentHolding],
        recommendations: List[RebalancingRecommendation],
        target_allocations: List[TargetAllocation]
    ) -> Decimal:
        """Рассчитать ожидаемое улучшение от ребалансировки"""
        
        # Текущее отклонение от целевого распределения
        current_deviation = Decimal("0")
        
        # TODO: Реализовать расчет метрик улучшения
        # - Снижение tracking error
        # - Улучшение Sharpe ratio
        # - Снижение концентрационного риска
        
        return Decimal("2.5")  # Временная заглушка
    
    def _calculate_risk_metrics(self, recommendations: List[RebalancingRecommendation]) -> Dict[str, Any]:
        """Рассчитать риск-метрики плана ребалансировки"""
        
        total_trades = len(recommendations)
        high_priority_trades = len([r for r in recommendations if r.priority >= 7])
        
        return {
            "total_trades": total_trades,
            "high_priority_trades": high_priority_trades,
            "market_impact_risk": "low" if total_trades <= 5 else "medium",
            "execution_complexity": "simple" if total_trades <= 3 else "complex"
        }
    
    def suggest_optimal_allocations(
        self,
        portfolio_id: int,
        risk_tolerance: str = "moderate",
        investment_horizon: int = 5
    ) -> List[TargetAllocation]:
        """Предложить оптимальные распределения на основе современной портфельной теории"""
        
        allocations = []
        
        if risk_tolerance == "conservative":
            # Консервативный портфель
            allocations = [
                TargetAllocation(asset_class="BOND", target_percent=Decimal("60")),
                TargetAllocation(asset_class="STOCK", target_percent=Decimal("30")),
                TargetAllocation(asset_class="real_estate", target_percent=Decimal("10"))
            ]
        elif risk_tolerance == "moderate":
            # Умеренный портфель
            allocations = [
                TargetAllocation(asset_class="STOCK", target_percent=Decimal("50")),
                TargetAllocation(asset_class="BOND", target_percent=Decimal("35")),
                TargetAllocation(asset_class="real_estate", target_percent=Decimal("10")),
                TargetAllocation(asset_class="alternative", target_percent=Decimal("5"))
            ]
        elif risk_tolerance == "aggressive":
            # Агрессивный портфель
            allocations = [
                TargetAllocation(asset_class="STOCK", target_percent=Decimal("70")),
                TargetAllocation(asset_class="BOND", target_percent=Decimal("15")),
                TargetAllocation(asset_class="real_estate", target_percent=Decimal("10")),
                TargetAllocation(asset_class="alternative", target_percent=Decimal("5"))
            ]
        
        # Корректируем на основе инвестиционного горизонта
        if investment_horizon > 10:
            # Долгосрочные инвестиции - больше акций
            for allocation in allocations:
                if allocation.asset_class == "STOCK":
                    allocation.target_percent += Decimal("10")
                elif allocation.asset_class == "BOND":
                    allocation.target_percent -= Decimal("10")
        
        return allocations
    
    def get_rebalancing_alerts(self, portfolio_id: int) -> List[Dict[str, Any]]:
        """Получить алерты о необходимости ребалансировки"""
        
        # TODO: Реализовать логику алертов
        # - Превышение порогов отклонения
        # - Календарные напоминания
        # - Значительные изменения рынка
        
        return []
    
    def simulate_rebalancing_scenarios(
        self,
        portfolio_id: int,
        scenarios: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Моделирование различных сценариев ребалансировки"""
        
        results = []
        
        for scenario in scenarios:
            # TODO: Реализовать симуляцию различных сценариев
            # - Стресс-тестирование
            # - Моделирование различных рыночных условий
            # - Оценка влияния на доходность и риск
            
            results.append({
                "scenario": scenario,
                "expected_return": Decimal("8.5"),
                "volatility": Decimal("12.3"),
                "max_drawdown": Decimal("15.2"),
                "sharpe_ratio": Decimal("0.69")
            })
        
        return results


class AutoRebalancingService:
    """Сервис автоматической ребалансировки"""
    
    def __init__(self, db: Session):
        self.db = db
        self.rebalancing_service = RebalancingService(db)
    
    def check_portfolios_for_rebalancing(self):
        """Проверить все портфели на необходимость ребалансировки"""
        
        # Получаем все портфели с включенной автоматической ребалансировкой
        # TODO: Добавить поле auto_rebalancing в модель Portfolio
        
        portfolios = self.db.query(Portfolio).filter(
            Portfolio.is_active == True
        ).all()
        
        for portfolio in portfolios:
            try:
                self._check_portfolio_rebalancing(portfolio.id)
            except Exception as e:
                print(f"Error checking portfolio {portfolio.id}: {e}")
    
    def _check_portfolio_rebalancing(self, portfolio_id: int):
        """Проверить конкретный портфель"""
        
        # TODO: Реализовать проверку условий автоматической ребалансировки
        # - Проверка временных интервалов
        # - Проверка порогов отклонения
        # - Отправка уведомлений пользователю
        
        pass
