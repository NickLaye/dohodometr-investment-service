"""
Анализатор дивидендных акций - поиск и оценка лучших дивидендных позиций.

Функции:
- Скрининг по дивидендной доходности
- Анализ стабильности выплат
- Качественные метрики компаний
- Прогнозирование дивидендов
- Календарь выплат
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import aiohttp
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class DividendGrade(Enum):
    """Оценка качества дивидендов"""
    EXCELLENT = "excellent"    # A+ (>4.5)
    GOOD = "good"             # A, B (3.5-4.5)
    AVERAGE = "average"       # C (2.5-3.5)
    POOR = "poor"             # D (1.5-2.5)
    RISKY = "risky"           # F (<1.5)


class SectorType(Enum):
    """Секторы экономики"""
    ENERGY = "energy"                    # Энергетика
    FINANCIALS = "financials"            # Финансы
    TELECOMMUNICATIONS = "telecom"       # Телекоммуникации
    UTILITIES = "utilities"              # Коммунальные услуги
    MATERIALS = "materials"              # Материалы
    INDUSTRIALS = "industrials"          # Промышленность
    CONSUMER_STAPLES = "consumer_staples" # Товары первой необходимости
    CONSUMER_DISCRETIONARY = "consumer_discretionary" # Товары длительного пользования
    TECHNOLOGY = "technology"            # Технологии
    HEALTHCARE = "healthcare"            # Здравоохранение
    REAL_ESTATE = "real_estate"         # Недвижимость


@dataclass
class DividendHistory:
    """История дивидендных выплат"""
    year: int
    quarters: List[Decimal]              # Выплаты по кварталам
    annual_total: Decimal                # Общая сумма за год
    yield_on_cost: Decimal               # Доходность от покупной цены
    payout_ratio: Optional[Decimal] = None  # Коэффициент выплат


@dataclass
class CompanyFinancials:
    """Финансовые показатели компании"""
    ticker: str
    company_name: str
    
    # Базовые метрики
    market_cap: Decimal
    current_price: Decimal
    book_value: Decimal
    
    # Доходность
    dividend_yield: Decimal              # Текущая дивидендная доходность
    dividend_per_share: Decimal          # Дивиденд на акцию
    
    # Финансовое здоровье
    debt_to_equity: Decimal              # Долг/собственный капитал
    current_ratio: Decimal               # Коэффициент текущей ликвидности
    roe: Decimal                         # Рентабельность собственного капитала
    
    # Рост
    revenue_growth: Decimal              # Рост выручки
    earnings_growth: Decimal             # Рост прибыли
    dividend_growth_5y: Decimal          # Рост дивидендов за 5 лет
    
    # Оценка
    pe_ratio: Decimal                    # P/E коэффициент
    pb_ratio: Decimal                    # P/B коэффициент
    payout_ratio: Decimal                # Коэффициент выплат
    
    # Мета-информация
    sector: SectorType
    country: str = "RU"
    currency: str = "RUB"


@dataclass
class DividendStock:
    """Дивидендная акция с оценкой"""
    financials: CompanyFinancials
    dividend_history: List[DividendHistory]
    
    # Оценки качества
    dividend_grade: DividendGrade
    stability_score: Decimal             # 0-10, стабильность выплат
    growth_score: Decimal                # 0-10, рост дивидендов
    financial_health_score: Decimal      # 0-10, финансовое здоровье
    overall_score: Decimal               # 0-10, общая оценка
    
    # Прогнозы
    next_ex_dividend_date: Optional[datetime] = None
    estimated_next_dividend: Optional[Decimal] = None
    dividend_yield_forecast: Optional[Decimal] = None
    
    # Риски
    risk_factors: List[str] = None
    analyst_recommendations: Dict[str, int] = None  # {"buy": 5, "hold": 3, "sell": 1}


@dataclass
class DividendScreenerFilters:
    """Фильтры для скрининга дивидендных акций"""
    min_dividend_yield: Optional[Decimal] = None      # Мин. дивидендная доходность
    max_dividend_yield: Optional[Decimal] = None      # Макс. дивидендная доходность
    min_market_cap: Optional[Decimal] = None          # Мин. капитализация
    min_dividend_years: Optional[int] = None          # Мин. лет выплат
    min_stability_score: Optional[Decimal] = None     # Мин. оценка стабильности
    max_payout_ratio: Optional[Decimal] = None        # Макс. коэффициент выплат
    sectors: Optional[List[SectorType]] = None        # Отрасли
    countries: Optional[List[str]] = None             # Страны
    min_current_ratio: Optional[Decimal] = None       # Мин. текущая ликвидность
    max_debt_to_equity: Optional[Decimal] = None      # Макс. долг/капитал


class DividendDataProvider:
    """Провайдер данных о дивидендах"""
    
    def __init__(self):
        self.moex_api_base = "https://iss.moex.com/iss"
        self.cache = {}
        self.cache_ttl = 3600  # 1 час
    
    async def get_russian_dividend_stocks(self) -> List[CompanyFinancials]:
        """Получить список российских дивидендных акций"""
        
        # Заглушка с реальными российскими компаниями
        russian_stocks = [
            CompanyFinancials(
                ticker="SBER",
                company_name="Сбербанк",
                market_cap=Decimal("7500000000000"),  # 7.5 трлн руб
                current_price=Decimal("285.50"),
                book_value=Decimal("450.0"),
                dividend_yield=Decimal("0.065"),      # 6.5%
                dividend_per_share=Decimal("18.50"),
                debt_to_equity=Decimal("0.15"),
                current_ratio=Decimal("1.2"),
                roe=Decimal("0.22"),
                revenue_growth=Decimal("0.12"),
                earnings_growth=Decimal("0.18"),
                dividend_growth_5y=Decimal("0.15"),
                pe_ratio=Decimal("4.5"),
                pb_ratio=Decimal("0.63"),
                payout_ratio=Decimal("0.30"),
                sector=SectorType.FINANCIALS
            ),
            CompanyFinancials(
                ticker="GAZP",
                company_name="Газпром",
                market_cap=Decimal("2800000000000"),  # 2.8 трлн руб
                current_price=Decimal("182.30"),
                book_value=Decimal("220.0"),
                dividend_yield=Decimal("0.089"),      # 8.9%
                dividend_per_share=Decimal("16.61"),
                debt_to_equity=Decimal("0.25"),
                current_ratio=Decimal("1.8"),
                roe=Decimal("0.18"),
                revenue_growth=Decimal("0.25"),
                earnings_growth=Decimal("0.30"),
                dividend_growth_5y=Decimal("0.12"),
                pe_ratio=Decimal("3.2"),
                pb_ratio=Decimal("0.83"),
                payout_ratio=Decimal("0.35"),
                sector=SectorType.ENERGY
            ),
            CompanyFinancials(
                ticker="LKOH",
                company_name="ЛУКОЙЛ",
                market_cap=Decimal("3200000000000"),  # 3.2 трлн руб
                current_price=Decimal("6420.0"),
                book_value=Decimal("4800.0"),
                dividend_yield=Decimal("0.078"),      # 7.8%
                dividend_per_share=Decimal("500.0"),
                debt_to_equity=Decimal("0.18"),
                current_ratio=Decimal("1.6"),
                roe=Decimal("0.25"),
                revenue_growth=Decimal("0.20"),
                earnings_growth=Decimal("0.28"),
                dividend_growth_5y=Decimal("0.18"),
                pe_ratio=Decimal("4.8"),
                pb_ratio=Decimal("1.34"),
                payout_ratio=Decimal("0.40"),
                sector=SectorType.ENERGY
            ),
            CompanyFinancials(
                ticker="ROSN",
                company_name="Роснефть",
                market_cap=Decimal("4500000000000"),  # 4.5 трлн руб
                current_price=Decimal("540.80"),
                book_value=Decimal("720.0"),
                dividend_yield=Decimal("0.072"),      # 7.2%
                dividend_per_share=Decimal("38.95"),
                debt_to_equity=Decimal("0.35"),
                current_ratio=Decimal("1.4"),
                roe=Decimal("0.16"),
                revenue_growth=Decimal("0.18"),
                earnings_growth=Decimal("0.22"),
                dividend_growth_5y=Decimal("0.10"),
                pe_ratio=Decimal("5.1"),
                pb_ratio=Decimal("0.75"),
                payout_ratio=Decimal("0.45"),
                sector=SectorType.ENERGY
            ),
            CompanyFinancials(
                ticker="NVTK",
                company_name="НОВАТЭК",
                market_cap=Decimal("3800000000000"),  # 3.8 трлн руб
                current_price=Decimal("1285.0"),
                book_value=Decimal("980.0"),
                dividend_yield=Decimal("0.054"),      # 5.4%
                dividend_per_share=Decimal("69.38"),
                debt_to_equity=Decimal("0.42"),
                current_ratio=Decimal("2.1"),
                roe=Decimal("0.28"),
                revenue_growth=Decimal("0.15"),
                earnings_growth=Decimal("0.20"),
                dividend_growth_5y=Decimal("0.22"),
                pe_ratio=Decimal("6.2"),
                pb_ratio=Decimal("1.31"),
                payout_ratio=Decimal("0.25"),
                sector=SectorType.ENERGY
            ),
            CompanyFinancials(
                ticker="TATN",
                company_name="Татнефть",
                market_cap=Decimal("1200000000000"),  # 1.2 трлн руб
                current_price=Decimal("685.50"),
                book_value=Decimal("820.0"),
                dividend_yield=Decimal("0.083"),      # 8.3%
                dividend_per_share=Decimal("56.90"),
                debt_to_equity=Decimal("0.22"),
                current_ratio=Decimal("1.9"),
                roe=Decimal("0.19"),
                revenue_growth=Decimal("0.14"),
                earnings_growth=Decimal("0.17"),
                dividend_growth_5y=Decimal("0.14"),
                pe_ratio=Decimal("4.7"),
                pb_ratio=Decimal("0.84"),
                payout_ratio=Decimal("0.42"),
                sector=SectorType.ENERGY
            ),
            CompanyFinancials(
                ticker="MTSS",
                company_name="МТС",
                market_cap=Decimal("550000000000"),   # 550 млрд руб
                current_price=Decimal("275.80"),
                book_value=Decimal("180.0"),
                dividend_yield=Decimal("0.098"),      # 9.8%
                dividend_per_share=Decimal("27.0"),
                debt_to_equity=Decimal("0.68"),
                current_ratio=Decimal("0.9"),
                roe=Decimal("0.24"),
                revenue_growth=Decimal("0.05"),
                earnings_growth=Decimal("0.08"),
                dividend_growth_5y=Decimal("0.08"),
                pe_ratio=Decimal("7.8"),
                pb_ratio=Decimal("1.53"),
                payout_ratio=Decimal("0.85"),
                sector=SectorType.TELECOMMUNICATIONS
            ),
            CompanyFinancials(
                ticker="MGNT",
                company_name="Магнит",
                market_cap=Decimal("980000000000"),   # 980 млрд руб
                current_price=Decimal("4250.0"),
                book_value=Decimal("2800.0"),
                dividend_yield=Decimal("0.041"),      # 4.1%
                dividend_per_share=Decimal("174.25"),
                debt_to_equity=Decimal("0.15"),
                current_ratio=Decimal("0.8"),
                roe=Decimal("0.12"),
                revenue_growth=Decimal("0.08"),
                earnings_growth=Decimal("0.06"),
                dividend_growth_5y=Decimal("0.05"),
                pe_ratio=Decimal("12.5"),
                pb_ratio=Decimal("1.52"),
                payout_ratio=Decimal("0.55"),
                sector=SectorType.CONSUMER_STAPLES
            )
        ]
        
        return russian_stocks
    
    async def get_dividend_history(self, ticker: str, years: int = 5) -> List[DividendHistory]:
        """Получить историю дивидендов"""
        # Заглушка с историческими данными
        history = []
        current_year = datetime.now().year
        
        # Симуляция истории дивидендов
        base_dividend = Decimal("15.0")
        growth_rate = Decimal("0.10")  # 10% рост в год
        
        for year in range(current_year - years, current_year):
            annual_dividend = base_dividend * (1 + growth_rate) ** (year - (current_year - years))
            
            # Разбиваем на кварталы (неравномерно)
            q1 = annual_dividend * Decimal("0.15")
            q2 = annual_dividend * Decimal("0.20")
            q3 = annual_dividend * Decimal("0.25")
            q4 = annual_dividend * Decimal("0.40")
            
            history.append(DividendHistory(
                year=year,
                quarters=[q1, q2, q3, q4],
                annual_total=annual_dividend,
                yield_on_cost=annual_dividend / Decimal("200.0"),  # Предполагаемая цена покупки
                payout_ratio=Decimal("0.35")
            ))
        
        return history


class DividendAnalyzer:
    """Анализатор дивидендных акций"""
    
    def __init__(self):
        self.data_provider = DividendDataProvider()
    
    def calculate_dividend_grade(self, stock: CompanyFinancials, 
                                history: List[DividendHistory]) -> DividendGrade:
        """Рассчитать оценку качества дивидендов"""
        score = Decimal("0")
        
        # Доходность (макс 2 балла)
        if stock.dividend_yield >= Decimal("0.08"):      # ≥8%
            score += Decimal("2.0")
        elif stock.dividend_yield >= Decimal("0.06"):    # ≥6%
            score += Decimal("1.5")
        elif stock.dividend_yield >= Decimal("0.04"):    # ≥4%
            score += Decimal("1.0")
        elif stock.dividend_yield >= Decimal("0.02"):    # ≥2%
            score += Decimal("0.5")
        
        # Стабильность выплат (макс 1.5 балла)
        if len(history) >= 5:
            increases = sum(1 for i in range(1, len(history)) 
                          if history[i].annual_total > history[i-1].annual_total)
            stability_ratio = increases / (len(history) - 1)
            score += Decimal(str(stability_ratio)) * Decimal("1.5")
        
        # Финансовое здоровье (макс 1.5 балла)
        health_score = Decimal("0")
        if stock.current_ratio >= Decimal("1.2"):
            health_score += Decimal("0.3")
        if stock.debt_to_equity <= Decimal("0.5"):
            health_score += Decimal("0.4")
        if stock.payout_ratio <= Decimal("0.6"):
            health_score += Decimal("0.4")
        if stock.roe >= Decimal("0.15"):
            health_score += Decimal("0.4")
        score += health_score
        
        # Оценка (макс 1 балл)
        if stock.pe_ratio <= Decimal("10"):
            score += Decimal("0.5")
        if stock.pb_ratio <= Decimal("1.5"):
            score += Decimal("0.5")
        
        # Определяем оценку
        if score >= Decimal("4.5"):
            return DividendGrade.EXCELLENT
        elif score >= Decimal("3.5"):
            return DividendGrade.GOOD
        elif score >= Decimal("2.5"):
            return DividendGrade.AVERAGE
        elif score >= Decimal("1.5"):
            return DividendGrade.POOR
        else:
            return DividendGrade.RISKY
    
    def calculate_stability_score(self, history: List[DividendHistory]) -> Decimal:
        """Рассчитать оценку стабильности дивидендов"""
        if len(history) < 2:
            return Decimal("0")
        
        # Анализируем изменения год к году
        changes = []
        for i in range(1, len(history)):
            if history[i-1].annual_total > 0:
                change = (history[i].annual_total - history[i-1].annual_total) / history[i-1].annual_total
                changes.append(float(change))
        
        if not changes:
            return Decimal("0")
        
        # Оценка на основе волатильности изменений
        volatility = np.std(changes)
        consistency = len([c for c in changes if c >= 0]) / len(changes)  # Доля положительных изменений
        
        # Базовая оценка от волатильности (меньше волатильность = выше оценка)
        volatility_score = max(0, 10 - volatility * 50)  # Скейлинг
        consistency_score = consistency * 10
        
        final_score = (volatility_score + consistency_score) / 2
        return Decimal(str(min(10.0, max(0.0, final_score))))
    
    def calculate_financial_health_score(self, stock: CompanyFinancials) -> Decimal:
        """Рассчитать оценку финансового здоровья"""
        score = Decimal("0")
        
        # Ликвидность (макс 2.5 балла)
        if stock.current_ratio >= Decimal("2.0"):
            score += Decimal("2.5")
        elif stock.current_ratio >= Decimal("1.5"):
            score += Decimal("2.0")
        elif stock.current_ratio >= Decimal("1.2"):
            score += Decimal("1.5")
        elif stock.current_ratio >= Decimal("1.0"):
            score += Decimal("1.0")
        
        # Долговая нагрузка (макс 2.5 балла)
        if stock.debt_to_equity <= Decimal("0.2"):
            score += Decimal("2.5")
        elif stock.debt_to_equity <= Decimal("0.4"):
            score += Decimal("2.0")
        elif stock.debt_to_equity <= Decimal("0.6"):
            score += Decimal("1.5")
        elif stock.debt_to_equity <= Decimal("1.0"):
            score += Decimal("1.0")
        
        # Рентабельность (макс 2.5 балла)
        if stock.roe >= Decimal("0.25"):
            score += Decimal("2.5")
        elif stock.roe >= Decimal("0.20"):
            score += Decimal("2.0")
        elif stock.roe >= Decimal("0.15"):
            score += Decimal("1.5")
        elif stock.roe >= Decimal("0.10"):
            score += Decimal("1.0")
        
        # Коэффициент выплат (макс 2.5 балла)
        if stock.payout_ratio <= Decimal("0.3"):
            score += Decimal("2.5")
        elif stock.payout_ratio <= Decimal("0.5"):
            score += Decimal("2.0")
        elif stock.payout_ratio <= Decimal("0.7"):
            score += Decimal("1.5")
        elif stock.payout_ratio <= Decimal("0.9"):
            score += Decimal("1.0")
        
        return min(Decimal("10"), score)
    
    async def analyze_dividend_stock(self, ticker: str) -> Optional[DividendStock]:
        """Полный анализ дивидендной акции"""
        try:
            # Получаем данные
            stocks = await self.data_provider.get_russian_dividend_stocks()
            stock_data = next((s for s in stocks if s.ticker == ticker), None)
            
            if not stock_data:
                return None
            
            history = await self.data_provider.get_dividend_history(ticker)
            
            # Рассчитываем оценки
            dividend_grade = self.calculate_dividend_grade(stock_data, history)
            stability_score = self.calculate_stability_score(history)
            financial_health_score = self.calculate_financial_health_score(stock_data)
            
            # Рост дивидендов
            growth_score = min(Decimal("10"), stock_data.dividend_growth_5y * Decimal("50"))
            
            # Общая оценка
            overall_score = (
                stability_score * Decimal("0.3") +
                financial_health_score * Decimal("0.3") +
                growth_score * Decimal("0.2") +
                (stock_data.dividend_yield * Decimal("100")) * Decimal("0.2")
            )
            overall_score = min(Decimal("10"), overall_score)
            
            # Прогноз следующего дивиденда
            if history:
                last_dividend = history[-1].annual_total
                estimated_next = last_dividend * (1 + stock_data.dividend_growth_5y / 5)
            else:
                estimated_next = stock_data.dividend_per_share
            
            # Факторы риска
            risk_factors = []
            if stock_data.payout_ratio > Decimal("0.8"):
                risk_factors.append("Высокий коэффициент выплат (>80%)")
            if stock_data.debt_to_equity > Decimal("0.6"):
                risk_factors.append("Высокая долговая нагрузка")
            if stock_data.current_ratio < Decimal("1.2"):
                risk_factors.append("Низкая ликвидность")
            if stock_data.sector == SectorType.ENERGY:
                risk_factors.append("Цикличность энергетического сектора")
            
            return DividendStock(
                financials=stock_data,
                dividend_history=history,
                dividend_grade=dividend_grade,
                stability_score=stability_score,
                growth_score=growth_score,
                financial_health_score=financial_health_score,
                overall_score=overall_score,
                estimated_next_dividend=estimated_next,
                risk_factors=risk_factors,
                analyst_recommendations={"buy": 8, "hold": 5, "sell": 2}  # Заглушка
            )
            
        except Exception as e:
            logger.error(f"Ошибка анализа акции {ticker}: {e}")
            return None
    
    async def screen_dividend_stocks(self, 
                                   filters: DividendScreenerFilters) -> List[DividendStock]:
        """Скрининг дивидендных акций по фильтрам"""
        all_stocks = await self.data_provider.get_russian_dividend_stocks()
        filtered_stocks = []
        
        for stock_data in all_stocks:
            # Применяем фильтры
            if filters.min_dividend_yield and stock_data.dividend_yield < filters.min_dividend_yield:
                continue
            if filters.max_dividend_yield and stock_data.dividend_yield > filters.max_dividend_yield:
                continue
            if filters.min_market_cap and stock_data.market_cap < filters.min_market_cap:
                continue
            if filters.max_payout_ratio and stock_data.payout_ratio > filters.max_payout_ratio:
                continue
            if filters.sectors and stock_data.sector not in filters.sectors:
                continue
            if filters.min_current_ratio and stock_data.current_ratio < filters.min_current_ratio:
                continue
            if filters.max_debt_to_equity and stock_data.debt_to_equity > filters.max_debt_to_equity:
                continue
            
            # Анализируем прошедшую фильтры акцию
            analyzed_stock = await self.analyze_dividend_stock(stock_data.ticker)
            if analyzed_stock:
                # Дополнительные фильтры по рассчитанным метрикам
                if filters.min_stability_score and analyzed_stock.stability_score < filters.min_stability_score:
                    continue
                
                filtered_stocks.append(analyzed_stock)
        
        # Сортируем по общей оценке
        filtered_stocks.sort(key=lambda x: x.overall_score, reverse=True)
        return filtered_stocks
    
    async def get_dividend_calendar(self, 
                                  months_ahead: int = 3) -> Dict[datetime, List[DividendStock]]:
        """Получить календарь дивидендных выплат"""
        calendar = {}
        stocks = await self.data_provider.get_russian_dividend_stocks()
        
        # Симулируем даты выплат
        base_date = datetime.now().replace(day=1)
        
        for i, stock_data in enumerate(stocks):
            analyzed_stock = await self.analyze_dividend_stock(stock_data.ticker)
            if analyzed_stock:
                # Предполагаем выплаты каждый квартал
                for month_offset in range(0, months_ahead, 3):
                    ex_date = base_date + timedelta(days=30 * month_offset + (i * 7) % 30)
                    
                    if ex_date not in calendar:
                        calendar[ex_date] = []
                    calendar[ex_date].append(analyzed_stock)
        
        return calendar
    
    def generate_dividend_report(self, stocks: List[DividendStock]) -> str:
        """Генерировать отчет по дивидендным акциям"""
        if not stocks:
            return "Акции не найдены по заданным критериям."
        
        report = f"""
ОТЧЕТ ПО ДИВИДЕНДНЫМ АКЦИЯМ
Дата: {datetime.now().strftime('%d.%m.%Y')}
Найдено акций: {len(stocks)}

=== ТОП-5 РЕКОМЕНДАЦИЙ ===
"""
        
        top_stocks = stocks[:5]
        for i, stock in enumerate(top_stocks, 1):
            grade_text = {
                DividendGrade.EXCELLENT: "Отлично",
                DividendGrade.GOOD: "Хорошо",
                DividendGrade.AVERAGE: "Средне",
                DividendGrade.POOR: "Плохо",
                DividendGrade.RISKY: "Рискованно"
            }[stock.dividend_grade]
            
            report += f"""
{i}. {stock.financials.company_name} ({stock.financials.ticker})
   💰 Дивидендная доходность: {stock.financials.dividend_yield:.1%}
   ⭐ Общая оценка: {stock.overall_score:.1f}/10
   📊 Качество дивидендов: {grade_text}
   🏛️ Стабильность: {stock.stability_score:.1f}/10
   💪 Финансовое здоровье: {stock.financial_health_score:.1f}/10
   📈 Рост дивидендов (5 лет): {stock.financials.dividend_growth_5y:.1%}
   💸 Коэффициент выплат: {stock.financials.payout_ratio:.1%}
   💵 Цена: {stock.financials.current_price} руб
"""

        report += f"""
=== СТАТИСТИКА ПО СЕКТОРАМ ===
"""
        
        # Группируем по секторам
        sectors = {}
        for stock in stocks:
            sector = stock.financials.sector
            if sector not in sectors:
                sectors[sector] = []
            sectors[sector].append(stock)
        
        for sector, sector_stocks in sectors.items():
            avg_yield = sum(s.financials.dividend_yield for s in sector_stocks) / len(sector_stocks)
            sector_name = {
                SectorType.ENERGY: "Энергетика",
                SectorType.FINANCIALS: "Финансы",
                SectorType.TELECOMMUNICATIONS: "Телекоммуникации",
                SectorType.UTILITIES: "Коммунальные услуги",
                SectorType.CONSUMER_STAPLES: "Товары первой необходимости"
            }.get(sector, sector.value)
            
            report += f"📊 {sector_name}: {len(sector_stocks)} акций, средняя доходность {avg_yield:.1%}\n"

        report += f"""
=== РЕКОМЕНДАЦИИ ПО ПОРТФЕЛЮ ===
• Диверсифицируйте между секторами (не более 30% в одном секторе)
• Отдавайте предпочтение компаниям с коэффициентом выплат <60%
• Следите за финансовым здоровьем: текущая ликвидность >1.2, долг/капитал <0.5
• Реинвестируйте дивиденды для ускорения роста капитала
• Регулярно пересматривайте портфель (раз в квартал)

=== НАЛОГОВЫЕ ОСОБЕННОСТИ ===
• Дивиденды российских компаний облагаются НДФЛ 13%
• При удержании налога у источника дополнительных действий не требуется
• Дивиденды от зарубежных компаний требуют подачи декларации
• ИИС типа Б освобождает от налога на дивиденды при выводе средств
        """
        
        return report.strip()


class DividendPortfolioOptimizer:
    """Оптимизатор дивидендного портфеля"""
    
    @staticmethod
    def optimize_for_yield(stocks: List[DividendStock], 
                          target_yield: Decimal,
                          max_single_position: Decimal = Decimal("0.15")) -> Dict[str, Decimal]:
        """
        Оптимизировать портфель для достижения целевой доходности
        
        Args:
            stocks: Список акций
            target_yield: Целевая дивидендная доходность
            max_single_position: Максимальная доля одной позиции
            
        Returns:
            Словарь с весами акций
        """
        # Фильтруем качественные акции
        quality_stocks = [s for s in stocks if s.overall_score >= Decimal("6.0")]
        
        if not quality_stocks:
            return {}
        
        # Сортируем по доходности
        quality_stocks.sort(key=lambda x: x.financials.dividend_yield, reverse=True)
        
        weights = {}
        total_weight = Decimal("0")
        current_yield = Decimal("0")
        
        for stock in quality_stocks:
            if total_weight >= Decimal("1.0"):
                break
            
            # Рассчитываем возможный вес
            remaining_weight = Decimal("1.0") - total_weight
            max_weight = min(max_single_position, remaining_weight)
            
            # Добавляем позицию
            weight = max_weight
            weights[stock.financials.ticker] = weight
            total_weight += weight
            
            # Обновляем текущую доходность портфеля
            current_yield = sum(
                weights[ticker] * next(s.financials.dividend_yield for s in quality_stocks if s.financials.ticker == ticker)
                for ticker in weights.keys()
            )
            
            if current_yield >= target_yield:
                break
        
        # Нормализуем веса
        if total_weight > 0:
            for ticker in weights:
                weights[ticker] = weights[ticker] / total_weight
        
        return weights
    
    @staticmethod
    def optimize_for_stability(stocks: List[DividendStock]) -> Dict[str, Decimal]:
        """Оптимизировать портфель для максимальной стабильности"""
        # Фильтруем стабильные акции
        stable_stocks = [s for s in stocks if s.stability_score >= Decimal("7.0")]
        
        if not stable_stocks:
            return {}
        
        # Равновесный портфель из топ стабильных акций
        top_stable = stable_stocks[:8]  # Топ 8 для диверсификации
        weight_per_stock = Decimal("1.0") / len(top_stable)
        
        return {stock.financials.ticker: weight_per_stock for stock in top_stable}
