"""
Продвинутая аналитическая система для инвестиционных портфелей.

Включает:
- Риск-метрики (Sharpe, Sortino, Beta, Alpha, VaR)
- Анализ корреляций и диверсификации
- Бектестинг стратегий
- Сравнение с бенчмарками
- Анализ drawdown'ов
- Стресс-тестирование
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class RiskMetric(Enum):
    """Типы риск-метрик"""
    SHARPE_RATIO = "sharpe_ratio"
    SORTINO_RATIO = "sortino_ratio"
    CALMAR_RATIO = "calmar_ratio"
    TREYNOR_RATIO = "treynor_ratio"
    INFORMATION_RATIO = "information_ratio"
    BETA = "beta"
    ALPHA = "alpha"
    VAR_95 = "var_95"
    VAR_99 = "var_99"
    CVAR_95 = "cvar_95"
    MAX_DRAWDOWN = "max_drawdown"
    VOLATILITY = "volatility"


class BenchmarkType(Enum):
    """Типы бенчмарков"""
    IMOEX = "imoex"           # Индекс МосБиржи
    RTSI = "rtsi"             # РТС индекс
    SP500 = "sp500"           # S&P 500
    NASDAQ = "nasdaq"         # NASDAQ
    MSCI_WORLD = "msci_world" # MSCI World
    CUSTOM = "custom"         # Пользовательский


@dataclass
class ReturnSeries:
    """Временной ряд доходностей"""
    dates: List[datetime]
    returns: List[float]
    cumulative_returns: List[float]
    portfolio_values: List[float]
    
    def to_pandas(self) -> pd.DataFrame:
        """Конвертация в pandas DataFrame"""
        return pd.DataFrame({
            'date': self.dates,
            'return': self.returns,
            'cumulative_return': self.cumulative_returns,
            'portfolio_value': self.portfolio_values
        }).set_index('date')


@dataclass
class RiskMetrics:
    """Результат расчета риск-метрик"""
    # Доходность
    total_return: float
    annualized_return: float
    cagr: float
    
    # Риск
    volatility: float
    downside_volatility: float
    max_drawdown: float
    average_drawdown: float
    
    # Риск-скорректированные метрики
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    
    # Рыночные метрики (относительно бенчмарка)
    beta: Optional[float] = None
    alpha: Optional[float] = None
    treynor_ratio: Optional[float] = None
    information_ratio: Optional[float] = None
    correlation: Optional[float] = None
    
    # Value at Risk
    var_95: float = None
    var_99: float = None
    cvar_95: float = None
    
    # Дополнительные метрики
    win_rate: float = None
    profit_factor: float = None
    maximum_gain: float = None
    maximum_loss: float = None
    
    # Статистика периодов
    period_days: int = None
    positive_periods: int = None
    negative_periods: int = None


@dataclass
class BacktestResult:
    """Результат бектестинга"""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    
    # Основные метрики
    total_return: float
    cagr: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    
    # Транзакции
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # Временные ряды
    equity_curve: ReturnSeries
    drawdown_series: List[float]
    
    # Сравнение с бенчмарком
    benchmark_return: Optional[float] = None
    excess_return: Optional[float] = None
    beta: Optional[float] = None
    alpha: Optional[float] = None
    
    # Детализация по периодам
    monthly_returns: Dict[str, float] = None
    yearly_returns: Dict[str, float] = None


class RiskCalculator:
    """Калькулятор риск-метрик"""
    
    @staticmethod
    def calculate_returns(prices: List[float]) -> List[float]:
        """Рассчитать доходности из цен"""
        if len(prices) < 2:
            return []
        
        returns = []
        for i in range(1, len(prices)):
            ret = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(ret)
        
        return returns
    
    @staticmethod
    def calculate_cumulative_returns(returns: List[float]) -> List[float]:
        """Рассчитать кумулятивные доходности"""
        cumulative = []
        cum_return = 1.0
        
        for ret in returns:
            cum_return *= (1 + ret)
            cumulative.append(cum_return - 1)
        
        return cumulative
    
    @staticmethod
    def calculate_sharpe_ratio(returns: List[float], 
                             risk_free_rate: float = 0.045) -> float:
        """
        Рассчитать коэффициент Шарпа
        
        Args:
            returns: Список доходностей
            risk_free_rate: Безрисковая ставка (по умолчанию 4.5% - ставка ЦБ РФ)
        """
        if not returns or len(returns) < 2:
            return 0.0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns, ddof=1)
        
        if std_return == 0:
            return 0.0
        
        # Аннуализируем (предполагаем дневные доходности)
        annualized_return = mean_return * 252
        annualized_volatility = std_return * np.sqrt(252)
        
        sharpe = (annualized_return - risk_free_rate) / annualized_volatility
        return float(sharpe)
    
    @staticmethod
    def calculate_sortino_ratio(returns: List[float], 
                              risk_free_rate: float = 0.045) -> float:
        """Рассчитать коэффициент Сортино"""
        if not returns or len(returns) < 2:
            return 0.0
        
        mean_return = np.mean(returns)
        negative_returns = [r for r in returns if r < 0]
        
        if not negative_returns:
            return float('inf')  # Нет отрицательных доходностей
        
        downside_deviation = np.std(negative_returns, ddof=1)
        
        if downside_deviation == 0:
            return 0.0
        
        annualized_return = mean_return * 252
        annualized_downside_deviation = downside_deviation * np.sqrt(252)
        
        sortino = (annualized_return - risk_free_rate) / annualized_downside_deviation
        return float(sortino)
    
    @staticmethod
    def calculate_beta(portfolio_returns: List[float], 
                      market_returns: List[float]) -> Optional[float]:
        """Рассчитать бету портфеля относительно рынка"""
        if (len(portfolio_returns) != len(market_returns) or 
            len(portfolio_returns) < 2):
            return None
        
        try:
            portfolio_array = np.array(portfolio_returns)
            market_array = np.array(market_returns)
            
            covariance = np.cov(portfolio_array, market_array)[0][1]
            market_variance = np.var(market_array, ddof=1)
            
            if market_variance == 0:
                return None
            
            beta = covariance / market_variance
            return float(beta)
            
        except Exception as e:
            logger.error(f"Ошибка при расчете беты: {e}")
            return None
    
    @staticmethod
    def calculate_alpha(portfolio_returns: List[float], 
                       market_returns: List[float],
                       risk_free_rate: float = 0.045) -> Optional[float]:
        """Рассчитать альфу по модели CAPM"""
        beta = RiskCalculator.calculate_beta(portfolio_returns, market_returns)
        if beta is None:
            return None
        
        portfolio_return = np.mean(portfolio_returns) * 252
        market_return = np.mean(market_returns) * 252
        
        alpha = portfolio_return - (risk_free_rate + beta * (market_return - risk_free_rate))
        return float(alpha)
    
    @staticmethod
    def calculate_max_drawdown(prices: List[float]) -> float:
        """Рассчитать максимальную просадку"""
        if len(prices) < 2:
            return 0.0
        
        peak = prices[0]
        max_dd = 0.0
        
        for price in prices:
            if price > peak:
                peak = price
            
            drawdown = (peak - price) / peak
            max_dd = max(max_dd, drawdown)
        
        return float(max_dd)
    
    @staticmethod
    def calculate_var(returns: List[float], confidence_level: float = 0.95) -> float:
        """Рассчитать Value at Risk"""
        if not returns:
            return 0.0
        
        return float(np.percentile(returns, (1 - confidence_level) * 100))
    
    @staticmethod
    def calculate_cvar(returns: List[float], confidence_level: float = 0.95) -> float:
        """Рассчитать Conditional Value at Risk"""
        if not returns:
            return 0.0
        
        var_threshold = RiskCalculator.calculate_var(returns, confidence_level)
        tail_losses = [r for r in returns if r <= var_threshold]
        
        if not tail_losses:
            return var_threshold
        
        return float(np.mean(tail_losses))


class AnalyticsEngine:
    """Основной аналитический движок"""
    
    def __init__(self):
        self.risk_calculator = RiskCalculator()
        self._benchmark_cache = {}
    
    async def calculate_portfolio_metrics(self,
                                        portfolio_values: List[float],
                                        dates: List[datetime],
                                        benchmark_returns: Optional[List[float]] = None) -> RiskMetrics:
        """
        Рассчитать полный набор риск-метрик для портфеля
        
        Args:
            portfolio_values: Стоимость портфеля по дням
            dates: Соответствующие даты
            benchmark_returns: Доходности бенчмарка (опционально)
        """
        if len(portfolio_values) < 2:
            return self._empty_metrics()
        
        # Рассчитываем доходности
        returns = self.risk_calculator.calculate_returns(portfolio_values)
        
        if not returns:
            return self._empty_metrics()
        
        # Базовые метрики доходности
        total_return = (portfolio_values[-1] - portfolio_values[0]) / portfolio_values[0]
        period_days = (dates[-1] - dates[0]).days
        
        if period_days == 0:
            annualized_return = 0.0
            cagr = 0.0
        else:
            years = period_days / 365.25
            annualized_return = np.mean(returns) * 252
            cagr = (portfolio_values[-1] / portfolio_values[0]) ** (1 / years) - 1
        
        # Риск-метрики
        volatility = np.std(returns, ddof=1) * np.sqrt(252)
        
        negative_returns = [r for r in returns if r < 0]
        downside_volatility = (np.std(negative_returns, ddof=1) * np.sqrt(252) 
                             if negative_returns else 0.0)
        
        max_drawdown = self.risk_calculator.calculate_max_drawdown(portfolio_values)
        
        # Риск-скорректированные метрики
        sharpe_ratio = self.risk_calculator.calculate_sharpe_ratio(returns)
        sortino_ratio = self.risk_calculator.calculate_sortino_ratio(returns)
        calmar_ratio = cagr / max_drawdown if max_drawdown > 0 else 0.0
        
        # VaR метрики
        var_95 = self.risk_calculator.calculate_var(returns, 0.95)
        var_99 = self.risk_calculator.calculate_var(returns, 0.99)
        cvar_95 = self.risk_calculator.calculate_cvar(returns, 0.95)
        
        # Дополнительные статистики
        positive_periods = len([r for r in returns if r > 0])
        negative_periods = len([r for r in returns if r < 0])
        win_rate = positive_periods / len(returns) if returns else 0.0
        
        positive_sum = sum([r for r in returns if r > 0])
        negative_sum = abs(sum([r for r in returns if r < 0]))
        profit_factor = positive_sum / negative_sum if negative_sum > 0 else float('inf')
        
        # Метрики относительно бенчмарка
        beta = None
        alpha = None
        treynor_ratio = None
        information_ratio = None
        correlation = None
        
        if benchmark_returns and len(benchmark_returns) == len(returns):
            beta = self.risk_calculator.calculate_beta(returns, benchmark_returns)
            alpha = self.risk_calculator.calculate_alpha(returns, benchmark_returns)
            
            if beta and beta != 0:
                treynor_ratio = (annualized_return - 0.045) / beta
            
            # Information Ratio
            excess_returns = [p - b for p, b in zip(returns, benchmark_returns)]
            if excess_returns and np.std(excess_returns, ddof=1) > 0:
                information_ratio = np.mean(excess_returns) / np.std(excess_returns, ddof=1) * np.sqrt(252)
            
            # Корреляция
            if len(returns) > 1:
                correlation, _ = stats.pearsonr(returns, benchmark_returns)
        
        return RiskMetrics(
            total_return=float(total_return),
            annualized_return=float(annualized_return),
            cagr=float(cagr),
            volatility=float(volatility),
            downside_volatility=float(downside_volatility),
            max_drawdown=float(max_drawdown),
            average_drawdown=float(np.mean([self._calculate_drawdown_at_point(portfolio_values, i) 
                                          for i in range(len(portfolio_values))])),
            sharpe_ratio=float(sharpe_ratio),
            sortino_ratio=float(sortino_ratio),
            calmar_ratio=float(calmar_ratio),
            beta=beta,
            alpha=alpha,
            treynor_ratio=treynor_ratio,
            information_ratio=information_ratio,
            correlation=correlation,
            var_95=float(var_95),
            var_99=float(var_99),
            cvar_95=float(cvar_95),
            win_rate=float(win_rate),
            profit_factor=float(profit_factor),
            maximum_gain=float(max(returns)) if returns else 0.0,
            maximum_loss=float(min(returns)) if returns else 0.0,
            period_days=period_days,
            positive_periods=positive_periods,
            negative_periods=negative_periods
        )
    
    def _calculate_drawdown_at_point(self, prices: List[float], index: int) -> float:
        """Рассчитать просадку на конкретную дату"""
        if index == 0:
            return 0.0
        
        peak = max(prices[:index + 1])
        return (peak - prices[index]) / peak
    
    def _empty_metrics(self) -> RiskMetrics:
        """Пустые метрики для случая недостатка данных"""
        return RiskMetrics(
            total_return=0.0,
            annualized_return=0.0,
            cagr=0.0,
            volatility=0.0,
            downside_volatility=0.0,
            max_drawdown=0.0,
            average_drawdown=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            calmar_ratio=0.0
        )
    
    async def backtest_strategy(self,
                              strategy_func,
                              price_data: pd.DataFrame,
                              initial_capital: float = 1000000,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None,
                              benchmark_data: Optional[pd.DataFrame] = None) -> BacktestResult:
        """
        Провести бектестинг торговой стратегии
        
        Args:
            strategy_func: Функция стратегии
            price_data: Исторические данные цен
            initial_capital: Начальный капитал
            start_date: Дата начала тестирования
            end_date: Дата окончания тестирования
            benchmark_data: Данные бенчмарка
        """
        # Фильтруем данные по датам
        if start_date:
            price_data = price_data[price_data.index >= start_date]
        if end_date:
            price_data = price_data[price_data.index <= end_date]
        
        if price_data.empty:
            raise ValueError("Нет данных для бектестинга в указанном периоде")
        
        # Инициализация
        portfolio_values = [initial_capital]
        positions = {}
        trades = []
        cash = initial_capital
        
        # Прогоняем стратегию по историческим данным
        for i, (date, row) in enumerate(price_data.iterrows()):
            # Получаем сигналы от стратегии
            signals = strategy_func(price_data.iloc[:i+1], positions, cash)
            
            # Исполняем торговые сигналы
            for symbol, signal in signals.items():
                if signal['action'] == 'BUY' and cash >= signal['amount']:
                    # Покупка
                    shares = signal['amount'] / row[symbol]
                    positions[symbol] = positions.get(symbol, 0) + shares
                    cash -= signal['amount']
                    trades.append({
                        'date': date,
                        'symbol': symbol,
                        'action': 'BUY',
                        'shares': shares,
                        'price': row[symbol],
                        'amount': signal['amount']
                    })
                
                elif signal['action'] == 'SELL' and symbol in positions and positions[symbol] > 0:
                    # Продажа
                    shares_to_sell = min(signal.get('shares', positions[symbol]), positions[symbol])
                    amount = shares_to_sell * row[symbol]
                    positions[symbol] -= shares_to_sell
                    cash += amount
                    trades.append({
                        'date': date,
                        'symbol': symbol,
                        'action': 'SELL',
                        'shares': shares_to_sell,
                        'price': row[symbol],
                        'amount': amount
                    })
            
            # Рассчитываем текущую стоимость портфеля
            portfolio_value = cash
            for symbol, shares in positions.items():
                if shares > 0:
                    portfolio_value += shares * row[symbol]
            
            portfolio_values.append(portfolio_value)
        
        # Анализируем результаты
        dates = [price_data.index[0]] + list(price_data.index)
        returns = self.risk_calculator.calculate_returns(portfolio_values)
        cumulative_returns = self.risk_calculator.calculate_cumulative_returns(returns)
        
        equity_curve = ReturnSeries(
            dates=dates,
            returns=[0] + returns,
            cumulative_returns=[0] + cumulative_returns,
            portfolio_values=portfolio_values
        )
        
        # Рассчитываем основные метрики
        total_return = (portfolio_values[-1] - initial_capital) / initial_capital
        period_days = (dates[-1] - dates[0]).days
        years = period_days / 365.25 if period_days > 0 else 1
        cagr = (portfolio_values[-1] / initial_capital) ** (1 / years) - 1
        
        volatility = np.std(returns, ddof=1) * np.sqrt(252) if len(returns) > 1 else 0
        sharpe_ratio = self.risk_calculator.calculate_sharpe_ratio(returns)
        max_drawdown = self.risk_calculator.calculate_max_drawdown(portfolio_values)
        
        # Анализ сделок
        buy_trades = [t for t in trades if t['action'] == 'BUY']
        sell_trades = [t for t in trades if t['action'] == 'SELL']
        
        # Упрощенный анализ прибыльности сделок
        winning_trades = 0
        losing_trades = 0
        
        # Группируем покупки и продажи по символам для анализа
        for symbol in set(t['symbol'] for t in trades):
            symbol_trades = [t for t in trades if t['symbol'] == symbol]
            symbol_trades.sort(key=lambda x: x['date'])
            
            # Простой FIFO анализ
            position = 0
            avg_price = 0
            
            for trade in symbol_trades:
                if trade['action'] == 'BUY':
                    if position == 0:
                        avg_price = trade['price']
                    else:
                        avg_price = (avg_price * position + trade['price'] * trade['shares']) / (position + trade['shares'])
                    position += trade['shares']
                
                elif trade['action'] == 'SELL' and position > 0:
                    pnl = (trade['price'] - avg_price) * trade['shares']
                    if pnl > 0:
                        winning_trades += 1
                    else:
                        losing_trades += 1
                    position -= trade['shares']
        
        total_trades = winning_trades + losing_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Сравнение с бенчмарком
        benchmark_return = None
        excess_return = None
        beta = None
        alpha = None
        
        if benchmark_data is not None:
            # Приводим бенчмарк к тому же периоду
            benchmark_period = benchmark_data[
                (benchmark_data.index >= dates[0]) & 
                (benchmark_data.index <= dates[-1])
            ]
            
            if not benchmark_period.empty:
                benchmark_values = benchmark_period.iloc[:, 0].values
                benchmark_returns = self.risk_calculator.calculate_returns(benchmark_values.tolist())
                benchmark_return = (benchmark_values[-1] - benchmark_values[0]) / benchmark_values[0]
                excess_return = total_return - benchmark_return
                
                if len(benchmark_returns) == len(returns):
                    beta = self.risk_calculator.calculate_beta(returns, benchmark_returns)
                    alpha = self.risk_calculator.calculate_alpha(returns, benchmark_returns)
        
        # Расчет просадок
        drawdown_series = []
        peak = portfolio_values[0]
        for value in portfolio_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            drawdown_series.append(drawdown)
        
        return BacktestResult(
            strategy_name="Custom Strategy",
            start_date=dates[0],
            end_date=dates[-1],
            initial_capital=initial_capital,
            final_capital=portfolio_values[-1],
            total_return=total_return,
            cagr=cagr,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            equity_curve=equity_curve,
            drawdown_series=drawdown_series,
            benchmark_return=benchmark_return,
            excess_return=excess_return,
            beta=beta,
            alpha=alpha
        )
    
    async def stress_test_portfolio(self,
                                  portfolio_weights: Dict[str, float],
                                  historical_data: pd.DataFrame,
                                  stress_scenarios: List[Dict]) -> Dict[str, Any]:
        """
        Провести стресс-тестирование портфеля
        
        Args:
            portfolio_weights: Веса активов в портфеле
            historical_data: Исторические данные
            stress_scenarios: Сценарии стресс-тестирования
        """
        results = {}
        
        for scenario in stress_scenarios:
            scenario_name = scenario['name']
            shocked_returns = self._apply_stress_scenario(historical_data, scenario)
            
            # Рассчитываем воздействие на портфель
            portfolio_impact = 0
            for asset, weight in portfolio_weights.items():
                if asset in shocked_returns:
                    portfolio_impact += weight * shocked_returns[asset]
            
            results[scenario_name] = {
                'portfolio_impact': portfolio_impact,
                'individual_impacts': {asset: shocked_returns.get(asset, 0) 
                                     for asset in portfolio_weights.keys()},
                'scenario_description': scenario.get('description', '')
            }
        
        return results
    
    def _apply_stress_scenario(self, data: pd.DataFrame, scenario: Dict) -> Dict[str, float]:
        """Применить сценарий стресс-тестирования"""
        shocked_returns = {}
        
        for asset in data.columns:
            base_return = 0  # Базовая доходность
            
            # Применяем шоки в зависимости от типа сценария
            if scenario['type'] == 'market_crash':
                # Рыночный крах - все активы падают
                shock = scenario.get('magnitude', -0.20)  # -20% по умолчанию
                shocked_returns[asset] = shock
            
            elif scenario['type'] == 'volatility_spike':
                # Рост волатильности
                historical_vol = data[asset].pct_change().std()
                vol_multiplier = scenario.get('multiplier', 2.0)
                shocked_returns[asset] = -historical_vol * vol_multiplier
            
            elif scenario['type'] == 'correlation_breakdown':
                # Разрыв корреляций - активы движутся независимо
                import random
                shocked_returns[asset] = random.uniform(-0.15, 0.15)
            
            elif scenario['type'] == 'custom':
                # Пользовательский сценарий
                asset_shocks = scenario.get('asset_shocks', {})
                shocked_returns[asset] = asset_shocks.get(asset, 0)
        
        return shocked_returns
    
    async def generate_analytics_report(self,
                                      portfolio_metrics: RiskMetrics,
                                      benchmark_metrics: Optional[RiskMetrics] = None,
                                      backtest_results: Optional[List[BacktestResult]] = None) -> str:
        """Генерировать комплексный аналитический отчет"""
        
        report = f"""
ПРОДВИНУТАЯ АНАЛИТИКА ПОРТФЕЛЯ
Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}

=== ОСНОВНЫЕ МЕТРИКИ ДОХОДНОСТИ ===
📈 Общая доходность: {portfolio_metrics.total_return:.2%}
📊 Годовая доходность: {portfolio_metrics.annualized_return:.2%}
🚀 CAGR: {portfolio_metrics.cagr:.2%}
📅 Период анализа: {portfolio_metrics.period_days} дней

=== РИСК-МЕТРИКИ ===
📉 Волатильность: {portfolio_metrics.volatility:.2%}
⬇️ Нисходящая волатильность: {portfolio_metrics.downside_volatility:.2%}
💥 Максимальная просадка: {portfolio_metrics.max_drawdown:.2%}
📊 Средняя просадка: {portfolio_metrics.average_drawdown:.2%}

=== РИСК-СКОРРЕКТИРОВАННАЯ ДОХОДНОСТЬ ===
⭐ Коэффициент Шарпа: {portfolio_metrics.sharpe_ratio:.3f}
🎯 Коэффициент Сортино: {portfolio_metrics.sortino_ratio:.3f}
📐 Коэффициент Кальмара: {portfolio_metrics.calmar_ratio:.3f}
"""

        # Рыночные метрики (если есть бенчмарк)
        if portfolio_metrics.beta is not None:
            report += f"""
=== РЫНОЧНЫЕ МЕТРИКИ ===
🔗 Бета: {portfolio_metrics.beta:.3f}
⚡ Альфа: {portfolio_metrics.alpha:.3f}
🎲 Коэффициент Трейнора: {portfolio_metrics.treynor_ratio:.3f}
📊 Информационный коэффициент: {portfolio_metrics.information_ratio:.3f}
🔄 Корреляция с рынком: {portfolio_metrics.correlation:.3f}
"""

        # Value at Risk
        report += f"""
=== VALUE AT RISK (VaR) ===
📉 VaR 95%: {portfolio_metrics.var_95:.2%}
💥 VaR 99%: {portfolio_metrics.var_99:.2%}
🔥 CVaR 95%: {portfolio_metrics.cvar_95:.2%}
"""

        # Статистика торговли
        report += f"""
=== СТАТИСТИКА ПЕРИОДОВ ===
✅ Положительных периодов: {portfolio_metrics.positive_periods}
❌ Отрицательных периодов: {portfolio_metrics.negative_periods}
🎯 Процент побед: {portfolio_metrics.win_rate:.1%}
💰 Фактор прибыли: {portfolio_metrics.profit_factor:.2f}
📈 Максимальная прибыль: {portfolio_metrics.maximum_gain:.2%}
📉 Максимальный убыток: {portfolio_metrics.maximum_loss:.2%}
"""

        # Сравнение с бенчмарком
        if benchmark_metrics:
            report += f"""
=== СРАВНЕНИЕ С БЕНЧМАРКОМ ===
                    Портфель    Бенчмарк    Превышение
Доходность:         {portfolio_metrics.cagr:.2%}      {benchmark_metrics.cagr:.2%}     {portfolio_metrics.cagr - benchmark_metrics.cagr:.2%}
Волатильность:      {portfolio_metrics.volatility:.2%}      {benchmark_metrics.volatility:.2%}     {portfolio_metrics.volatility - benchmark_metrics.volatility:.2%}
Шарп:              {portfolio_metrics.sharpe_ratio:.3f}        {benchmark_metrics.sharpe_ratio:.3f}       {portfolio_metrics.sharpe_ratio - benchmark_metrics.sharpe_ratio:.3f}
Макс. просадка:     {portfolio_metrics.max_drawdown:.2%}      {benchmark_metrics.max_drawdown:.2%}     {portfolio_metrics.max_drawdown - benchmark_metrics.max_drawdown:.2%}
"""

        # Результаты бектестинга
        if backtest_results:
            report += f"""
=== РЕЗУЛЬТАТЫ БЕКТЕСТИНГА ===
"""
            for result in backtest_results:
                report += f"""
Стратегия: {result.strategy_name}
Период: {result.start_date.strftime('%d.%m.%Y')} - {result.end_date.strftime('%d.%m.%Y')}
Начальный капитал: {result.initial_capital:,.0f} руб
Финальный капитал: {result.final_capital:,.0f} руб
Общая доходность: {result.total_return:.2%}
CAGR: {result.cagr:.2%}
Шарп: {result.sharpe_ratio:.3f}
Максимальная просадка: {result.max_drawdown:.2%}
Всего сделок: {result.total_trades}
Процент прибыльных: {result.win_rate:.1%}
"""

        # Рекомендации
        report += f"""
=== АНАЛИТИЧЕСКИЕ ВЫВОДЫ ===
"""
        
        # Анализ уровня риска
        if portfolio_metrics.volatility < 0.15:
            risk_level = "Низкий"
        elif portfolio_metrics.volatility < 0.25:
            risk_level = "Умеренный"
        else:
            risk_level = "Высокий"
        
        report += f"🎯 Уровень риска портфеля: {risk_level}\n"
        
        # Рекомендации по Шарпу
        if portfolio_metrics.sharpe_ratio > 1.0:
            report += "⭐ Отличное соотношение риска и доходности (Шарп > 1.0)\n"
        elif portfolio_metrics.sharpe_ratio > 0.5:
            report += "✅ Хорошее соотношение риска и доходности\n"
        else:
            report += "⚠️ Низкое соотношение риска и доходности - рассмотрите оптимизацию\n"
        
        # Рекомендации по просадке
        if portfolio_metrics.max_drawdown > 0.20:
            report += "💥 Высокая максимальная просадка - рассмотрите стратегии хеджирования\n"
        elif portfolio_metrics.max_drawdown > 0.10:
            report += "⚠️ Умеренная просадка - контролируйте риски\n"
        else:
            report += "✅ Низкая просадка - хорошее управление рисками\n"
        
        # Рекомендации по бете
        if portfolio_metrics.beta is not None:
            if portfolio_metrics.beta > 1.2:
                report += "📈 Высокая бета - портфель более волатилен чем рынок\n"
            elif portfolio_metrics.beta < 0.8:
                report += "📉 Низкая бета - портфель менее волатилен чем рынок\n"
            else:
                report += "⚖️ Умеренная бета - портфель движется в соответствии с рынком\n"
        
        report += """
=== СЛЕДУЮЩИЕ ШАГИ ===
• Регулярно пересматривайте метрики риска
• Рассмотрите ребалансировку при отклонении от целевых весов
• Используйте стресс-тестирование для проверки устойчивости
• Мониторьте корреляции между активами
• Оценивайте эффективность относительно бенчмарков
        """
        
        return report.strip()


# Фабричные функции для создания стандартных стратегий
def create_buy_and_hold_strategy(symbols: List[str], weights: Dict[str, float]):
    """Создать стратегию 'купи и держи'"""
    def strategy(data, positions, cash):
        signals = {}
        if len(data) == 1:  # Первый день - покупаем
            for symbol in symbols:
                if symbol in data.columns:
                    target_amount = cash * weights.get(symbol, 0)
                    signals[symbol] = {'action': 'BUY', 'amount': target_amount}
        return signals
    return strategy


def create_rebalancing_strategy(symbols: List[str], 
                              weights: Dict[str, float], 
                              rebalance_frequency: int = 60):
    """Создать стратегию с периодическим ребалансированием"""
    def strategy(data, positions, cash):
        signals = {}
        if len(data) % rebalance_frequency == 1 or len(data) == 1:
            total_value = cash + sum(positions.get(s, 0) * data.iloc[-1][s] 
                                   for s in symbols if s in data.columns)
            
            for symbol in symbols:
                if symbol in data.columns:
                    target_value = total_value * weights.get(symbol, 0)
                    current_value = positions.get(symbol, 0) * data.iloc[-1][symbol]
                    
                    if target_value > current_value:
                        # Покупаем
                        signals[symbol] = {'action': 'BUY', 'amount': target_value - current_value}
                    elif current_value > target_value * 1.05:  # 5% допуск
                        # Продаем
                        shares_to_sell = (current_value - target_value) / data.iloc[-1][symbol]
                        signals[symbol] = {'action': 'SELL', 'shares': shares_to_sell}
        
        return signals
    return strategy
