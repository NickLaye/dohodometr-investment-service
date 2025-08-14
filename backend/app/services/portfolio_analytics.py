"""
Сервис для расчета аналитики портфелей.
"""

import math
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta, date
from dataclasses import dataclass

import numpy as np
from scipy.optimize import fsolve
import pandas as pd

from app.core.logging import logger


@dataclass
class CashFlow:
    """Денежный поток для расчета XIRR."""
    date: date
    amount: Decimal
    description: str = ""


@dataclass
class PricePoint:
    """Точка цены для расчета доходности."""
    date: date
    value: Decimal


@dataclass
class PerformanceMetrics:
    """Метрики производительности портфеля."""
    twr_1d: Optional[Decimal] = None
    twr_1w: Optional[Decimal] = None
    twr_1m: Optional[Decimal] = None
    twr_3m: Optional[Decimal] = None
    twr_6m: Optional[Decimal] = None
    twr_1y: Optional[Decimal] = None
    twr_3y: Optional[Decimal] = None
    twr_5y: Optional[Decimal] = None
    twr_inception: Optional[Decimal] = None
    
    xirr: Optional[Decimal] = None
    
    volatility: Optional[Decimal] = None
    sharpe_ratio: Optional[Decimal] = None
    max_drawdown: Optional[Decimal] = None
    
    total_return: Optional[Decimal] = None
    annualized_return: Optional[Decimal] = None


class PortfolioAnalyticsService:
    """Сервис для расчета аналитики портфелей."""
    
    def __init__(self, db_session=None):
        self.risk_free_rate = Decimal('0.04')  # 4% годовых безрисковая ставка
        self.db = db_session
    
    # --------- Методы, к которым обращаются тесты (заглушки с ожидаемыми сигнатурами) ---------
    def get_portfolio_holdings(self, portfolio_id: int) -> List[Dict[str, Any]]:
        """Возвращает текущие холдинги портфеля. В тестах замещается patch.object(...)."""
        return []
    
    def get_portfolio_historical_values(self, portfolio_id: int) -> List[Dict[str, Any]]:
        """Возвращает исторические значения портфеля для расчета доходности. В тестах замещается patch."""
        return []
    
    def get_portfolio_cash_flows(self, portfolio_id: int) -> List[Dict[str, Any]]:
        """Возвращает денежные потоки по портфелю. В тестах замещается patch."""
        return []
    # -----------------------------------------------------------------------------------------
    
    def calculate_twr(
        self,
        price_points: List[PricePoint],
        cash_flows: List[CashFlow],
        period_days: int
    ) -> Optional[Decimal]:
        """
        Расчет Time-Weighted Return (TWR).
        TWR исключает влияние притоков/оттоков капитала.
        """
        if len(price_points) < 2:
            return None
        
        try:
            # Сортируем данные по дате
            price_points = sorted(price_points, key=lambda x: x.date)
            cash_flows = sorted(cash_flows, key=lambda x: x.date)
            
            # Фильтруем по периоду
            end_date = price_points[-1].date
            start_date = end_date - timedelta(days=period_days)
            
            filtered_prices = [p for p in price_points if p.date >= start_date]
            filtered_cashflows = [cf for cf in cash_flows if start_date <= cf.date <= end_date]
            
            if len(filtered_prices) < 2:
                return None
            
            # Создаем серию цен с учетом денежных потоков
            twr = Decimal('1.0')
            
            for i in range(len(filtered_prices) - 1):
                current_value = filtered_prices[i].value
                next_value = filtered_prices[i + 1].value
                current_date = filtered_prices[i].date
                next_date = filtered_prices[i + 1].date
                
                # Находим денежные потоки между датами
                period_cashflows = [cf for cf in filtered_cashflows if current_date < cf.date <= next_date]
                
                # Корректируем на денежные потоки
                total_cashflow = sum(cf.amount for cf in period_cashflows)
                adjusted_current_value = current_value + total_cashflow
                
                if adjusted_current_value > 0:
                    period_return = next_value / adjusted_current_value
                    twr *= period_return
            
            # Конвертируем в процентную доходность
            twr_percent = (twr - 1) * 100
            
            # Аннуализируем если период больше года
            if period_days > 365:
                years = period_days / 365.25
                twr_percent = ((1 + twr_percent / 100) ** (1 / years) - 1) * 100
            
            return twr_percent
            
        except Exception as e:
            logger.error(f"Ошибка расчета TWR: {e}")
            return None
    
    def calculate_xirr(self, cash_flows: List[CashFlow]) -> Optional[Decimal]:
        """
        Расчет XIRR (Extended Internal Rate of Return).
        Находит внутреннюю норму доходности с учетом дат денежных потоков.
        """
        if len(cash_flows) < 2:
            return None
        
        try:
            # Сортируем по дате
            cash_flows = sorted(cash_flows, key=lambda x: x.date)
            
            # Конвертируем в numpy массивы
            dates = [cf.date for cf in cash_flows]
            amounts = [float(cf.amount) for cf in cash_flows]
            
            # Базовая дата (первая дата)
            base_date = dates[0]
            
            # Конвертируем даты в количество дней от базовой даты
            days = [(d - base_date).days for d in dates]
            
            # Функция для поиска XIRR
            def xirr_equation(rate):
                return sum(
                    amount / ((1 + rate) ** (day / 365.25))
                    for amount, day in zip(amounts, days)
                )
            
            # Ищем корень уравнения
            try:
                rate = fsolve(xirr_equation, 0.1)[0]  # Начальное приближение 10%
                
                # Проверяем разумность результата (-100% < XIRR < 1000%)
                if -1 <= rate <= 10:
                    return Decimal(str(rate * 100))  # Конвертируем в проценты
                else:
                    return None
                    
            except:
                return None
                
        except Exception as e:
            logger.error(f"Ошибка расчета XIRR: {e}")
            return None
    
    def calculate_volatility(
        self,
        price_points: List[PricePoint],
        period_days: int = 252  # Торговых дней в году
    ) -> Optional[Decimal]:
        """Расчет волатильности (стандартное отклонение доходностей)."""
        if len(price_points) < 2:
            return None
        
        try:
            # Сортируем по дате
            price_points = sorted(price_points, key=lambda x: x.date)
            
            # Рассчитываем дневные доходности
            returns = []
            for i in range(1, len(price_points)):
                prev_value = float(price_points[i-1].value)
                curr_value = float(price_points[i].value)
                
                if prev_value > 0:
                    daily_return = (curr_value - prev_value) / prev_value
                    returns.append(daily_return)
            
            if len(returns) < 2:
                return None
            
            # Рассчитываем стандартное отклонение
            returns_array = np.array(returns)
            volatility = np.std(returns_array, ddof=1)
            
            # Аннуализируем (умножаем на корень из количества торговых дней)
            annualized_volatility = volatility * math.sqrt(period_days)
            
            return Decimal(str(annualized_volatility * 100))  # В процентах
            
        except Exception as e:
            logger.error(f"Ошибка расчета волатильности: {e}")
            return None
    
    def calculate_sharpe_ratio(
        self,
        portfolio_return: Decimal,
        volatility: Decimal,
        risk_free_rate: Optional[Decimal] = None
    ) -> Optional[Decimal]:
        """Расчет коэффициента Шарпа."""
        if volatility <= 0:
            return None
        
        try:
            rf_rate = risk_free_rate or self.risk_free_rate
            excess_return = portfolio_return - rf_rate
            sharpe = excess_return / volatility
            
            return sharpe
            
        except Exception as e:
            logger.error(f"Ошибка расчета коэффициента Шарпа: {e}")
            return None
    
    def calculate_max_drawdown(self, price_points: List[PricePoint]) -> Optional[Decimal]:
        """Расчет максимальной просадки."""
        if len(price_points) < 2:
            return None
        
        try:
            # Сортируем по дате
            price_points = sorted(price_points, key=lambda x: x.date)
            values = [float(p.value) for p in price_points]
            
            # Находим максимальную просадку
            peak = values[0]
            max_drawdown = 0
            
            for value in values[1:]:
                if value > peak:
                    peak = value
                
                drawdown = (peak - value) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            return Decimal(str(max_drawdown * 100))  # В процентах
            
        except Exception as e:
            logger.error(f"Ошибка расчета максимальной просадки: {e}")
            return None
    
    def calculate_portfolio_metrics(
        self,
        price_points: List[PricePoint],
        cash_flows: List[CashFlow]
    ) -> PerformanceMetrics:
        """Расчет всех метрик производительности портфеля."""
        
        metrics = PerformanceMetrics()
        
        # Расчет TWR для разных периодов
        periods = {
            'twr_1d': 1,
            'twr_1w': 7,
            'twr_1m': 30,
            'twr_3m': 90,
            'twr_6m': 180,
            'twr_1y': 365,
            'twr_3y': 365 * 3,
            'twr_5y': 365 * 5,
        }
        
        for metric_name, days in periods.items():
            twr = self.calculate_twr(price_points, cash_flows, days)
            setattr(metrics, metric_name, twr)
        
        # TWR с момента создания портфеля
        if len(price_points) >= 2:
            inception_days = (price_points[-1].date - price_points[0].date).days
            metrics.twr_inception = self.calculate_twr(price_points, cash_flows, inception_days)
        
        # XIRR
        metrics.xirr = self.calculate_xirr(cash_flows)
        
        # Волатильность
        metrics.volatility = self.calculate_volatility(price_points)
        
        # Коэффициент Шарпа
        if metrics.twr_1y and metrics.volatility:
            metrics.sharpe_ratio = self.calculate_sharpe_ratio(
                metrics.twr_1y, metrics.volatility
            )
        
        # Максимальная просадка
        metrics.max_drawdown = self.calculate_max_drawdown(price_points)
        
        # Общая доходность
        if len(price_points) >= 2:
            initial_value = price_points[0].value
            final_value = price_points[-1].value
            if initial_value > 0:
                metrics.total_return = ((final_value - initial_value) / initial_value) * 100
        
        # Аннуализированная доходность
        if metrics.total_return and len(price_points) >= 2:
            days_held = (price_points[-1].date - price_points[0].date).days
            if days_held > 0:
                years = days_held / 365.25
                annualized = ((1 + metrics.total_return / 100) ** (1 / years) - 1) * 100
                metrics.annualized_return = annualized
        
        return metrics
    
    def calculate_allocation_by_sector(self, portfolio_id: int) -> Dict[str, float]:
        """Утилита для тестов: вычисление распределения по секторам из текущих холдингов."""
        holdings = self.get_portfolio_holdings(portfolio_id)
        total_value = sum(h.get("value") or h.get("market_value") or 0 for h in holdings)
        if not total_value:
            return {}
        per_sector: Dict[str, float] = {}
        for h in holdings:
            sector = h.get("sector", "unknown")
            value = h.get("value") or h.get("market_value") or 0
            per_sector[sector] = per_sector.get(sector, 0) + value
        return {k: round(v / total_value * 100, 2) for k, v in per_sector.items()}
