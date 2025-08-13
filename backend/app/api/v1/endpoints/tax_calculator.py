"""API эндпоинт для налогового калькулятора РФ."""

from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from decimal import Decimal

from app.core.security import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.tax_calculator_rf import (
    TaxCalculatorRF, 
    TaxCalculationResult,
    calculate_optimal_iis_strategy,
    generate_tax_optimization_recommendations
)
from app.repositories.portfolio import PortfolioRepository
from app.repositories.transaction import TransactionRepository

router = APIRouter()


@router.get("/")
async def tax_module_info():
    """Информация о налоговом модуле."""
    return {
        "module": "Tax Calculator RF",
        "version": "1.0.0",
        "description": "Калькулятор налогов для российских инвесторов",
        "endpoints": {
            "calculate": "POST /calculate - Расчет налогов для портфелей",
            "iis_strategy": "POST /iis-strategy - Оптимальная стратегия ИИС",
            "demo_calculation": "GET /demo-calculation - Демо расчет",
            "tax_deadlines": "GET /tax-deadlines - Налоговые сроки",
            "tax_rates": "GET /tax-rates - Актуальные ставки",
            "health": "GET /health - Проверка работоспособности"
        },
        "features": [
            "НДФЛ расчет для резидентов и нерезидентов",
            "Оптимизация ИИС типа А и Б",
            "Льгота долгосрочного владения (ЛДВ)",
            "Зачет убытков между операциями",
            "Дивидендные и купонные доходы"
        ]
    }


class TaxCalculationRequest(BaseModel):
    """Запрос расчета налогов."""
    portfolio_ids: List[int] = Field(..., description="ID портфелей для расчета")
    tax_year: Optional[int] = Field(None, description="Налоговый год (по умолчанию текущий)")
    is_resident: bool = Field(True, description="Является ли налогоплательщик резидентом РФ")


class TaxCalculationResponse(BaseModel):
    """Ответ с результатами расчета налогов."""
    # Основные показатели
    total_income: float = Field(..., description="Общий доход, руб")
    total_expenses: float = Field(..., description="Общие расходы, руб")
    taxable_income: float = Field(..., description="Налогооблагаемый доход, руб")
    
    # НДФЛ
    ndfl_base: float = Field(..., description="База для НДФЛ, руб")
    ndfl_amount: float = Field(..., description="НДФЛ к доплате, руб")
    ndfl_rate: float = Field(..., description="Ставка НДФЛ")
    
    # Льготы
    ldv_exemption: float = Field(..., description="Льгота долгосрочного владения, руб")
    iis_deduction: float = Field(..., description="Вычет по ИИС, руб")
    loss_carryover: float = Field(..., description="Перенос убытков, руб")
    
    # Детализация по типам
    stock_pnl: float = Field(..., description="P&L по акциям, руб")
    bond_pnl: float = Field(..., description="P&L по облигациям, руб")
    dividend_income: float = Field(..., description="Доходы от дивидендов, руб")
    coupon_income: float = Field(..., description="Доходы от купонов, руб")
    
    # Мета информация
    tax_year: int = Field(..., description="Налоговый год")
    calculation_date: str = Field(..., description="Дата расчета")
    recommendations: List[str] = Field(..., description="Рекомендации по оптимизации")


class IISStrategyRequest(BaseModel):
    """Запрос расчета оптимальной стратегии ИИС."""
    annual_income: float = Field(..., description="Годовой доход, руб")
    expected_return: float = Field(..., description="Ожидаемая доходность портфеля, %")
    investment_horizon: int = Field(..., description="Горизонт инвестирования, лет")
    annual_contribution: float = Field(400000, description="Годовой взнос на ИИС, руб")


class IISStrategyResponse(BaseModel):
    """Ответ с оптимальной стратегией ИИС."""
    type_a_net_result: float = Field(..., description="Итоговая сумма по ИИС типа А")
    type_b_net_result: float = Field(..., description="Итоговая сумма по ИИС типа Б")
    type_a_deductions: float = Field(..., description="Общая сумма вычетов по типу А")
    type_a_ndfl: float = Field(..., description="НДФЛ к доплате по типу А")
    type_b_ndfl: float = Field(..., description="НДФЛ к доплате по типу Б")
    optimal_strategy: str = Field(..., description="Оптимальная стратегия (A или B)")
    advantage_amount: float = Field(..., description="Преимущество в рублях")


@router.post("/calculate", response_model=TaxCalculationResponse)
async def calculate_taxes(
    request: TaxCalculationRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Рассчитать налоги для указанных портфелей.
    
    Производит полный расчет налогообложения в соответствии с НК РФ:
    - НДФЛ 13% с доходов от инвестиций
    - Льготы по ИИС типа А и Б
    - Льгота на долгосрочное владение (ЛДВ)
    - Зачет убытков между операциями
    """
    
    # Проверяем доступ к портфелям
    portfolio_repo = PortfolioRepository(db)
    portfolios = []
    
    for portfolio_id in request.portfolio_ids:
        portfolio = await portfolio_repo.get_by_id(portfolio_id)
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Портфель {portfolio_id} не найден"
            )
        
        if portfolio.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Нет доступа к портфелю {portfolio_id}"
            )
        
        portfolios.append(portfolio)
    
    # Получаем все транзакции за налоговый год
    tax_year = request.tax_year or datetime.now().year
    transaction_repo = TransactionRepository(db)
    
    all_transactions = []
    for portfolio in portfolios:
        transactions = await transaction_repo.get_portfolio_transactions(
            portfolio_id=portfolio.id,
            start_date=datetime(tax_year, 1, 1),
            end_date=datetime(tax_year, 12, 31, 23, 59, 59)
        )
        all_transactions.extend(transactions)
    
    # Инициализируем калькулятор
    calculator = TaxCalculatorRF(is_resident=request.is_resident)
    
    # Рассчитываем налоги
    result = calculator.calculate_taxes(
        transactions=all_transactions,
        portfolios=portfolios,
        tax_year=tax_year
    )
    
    # Конвертируем результат в ответ API
    return TaxCalculationResponse(
        total_income=float(result.total_income),
        total_expenses=float(result.total_expenses),
        taxable_income=float(result.taxable_income),
        ndfl_base=float(result.ndfl_base),
        ndfl_amount=float(result.ndfl_amount),
        ndfl_rate=float(result.ndfl_rate),
        ldv_exemption=float(result.ldv_exemption),
        iis_deduction=float(result.iis_deduction),
        loss_carryover=float(result.loss_carryover),
        stock_pnl=float(result.stock_pnl),
        bond_pnl=float(result.bond_pnl),
        dividend_income=float(result.dividend_income),
        coupon_income=float(result.coupon_income),
        tax_year=tax_year,
        calculation_date=datetime.now().isoformat(),
        recommendations=result.recommendations
    )


@router.post("/iis-strategy", response_model=IISStrategyResponse)
async def calculate_iis_strategy(
    request: IISStrategyRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Рассчитать оптимальную стратегию ИИС.
    
    Сравнивает эффективность ИИС типа А (вычет на взносы) 
    и типа Б (освобождение доходов) для заданных параметров.
    """
    
    result = calculate_optimal_iis_strategy(
        annual_income=Decimal(str(request.annual_income)),
        expected_portfolio_return=Decimal(str(request.expected_return / 100)),
        investment_horizon_years=request.investment_horizon,
        annual_contribution=Decimal(str(request.annual_contribution))
    )
    
    return IISStrategyResponse(
        type_a_net_result=float(result["type_a_net_result"]),
        type_b_net_result=float(result["type_b_net_result"]),
        type_a_deductions=float(result["type_a_deductions"]),
        type_a_ndfl=float(result["type_a_ndfl"]),
        type_b_ndfl=float(result["type_b_ndfl"]),
        optimal_strategy=result["optimal_strategy"],
        advantage_amount=float(result["advantage_amount"])
    )


@router.get("/demo-calculation")
async def demo_tax_calculation():
    """
    Демонстрационный расчет налогов на примере типичного портфеля.
    
    Показывает возможности налогового калькулятора без необходимости 
    регистрации и создания портфеля.
    """
    
    # Создаем демо данные
    from app.models.transaction import Transaction, TransactionType
    from decimal import Decimal
    
    demo_transactions = [
        # Покупки акций
        Transaction(
            symbol="SBER",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("100"),
            price=Decimal("250.50"),
            total_amount=Decimal("25050"),
            commission=Decimal("25"),
            currency="RUB",
            executed_at=datetime(2024, 3, 15)
        ),
        Transaction(
            symbol="GAZP",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("50"),
            price=Decimal("180.75"),
            total_amount=Decimal("9037.50"),
            commission=Decimal("18"),
            currency="RUB",
            executed_at=datetime(2024, 4, 20)
        ),
        
        # Продажа с прибылью
        Transaction(
            symbol="SBER",
            transaction_type=TransactionType.SELL,
            quantity=Decimal("50"),
            price=Decimal("280.00"),
            total_amount=Decimal("14000"),
            commission=Decimal("28"),
            currency="RUB",
            executed_at=datetime(2024, 11, 10)
        ),
        
        # Дивиденды
        Transaction(
            symbol="SBER",
            transaction_type=TransactionType.DIVIDEND,
            quantity=Decimal("50"),
            price=Decimal("18.70"),
            total_amount=Decimal("935"),
            commission=Decimal("0"),
            currency="RUB",
            executed_at=datetime(2024, 7, 15)
        ),
    ]
    
    # Рассчитываем
    calculator = TaxCalculatorRF(is_resident=True)
    result = calculator.calculate_taxes(
        transactions=demo_transactions,
        portfolios=[],  # Для демо портфели не нужны
        tax_year=2024
    )
    
    return {
        "demo": True,
        "description": "Пример расчета налогов для типичного частного инвестора",
        "portfolio_summary": {
            "stocks_bought": "SBER (100 шт), GAZP (50 шт)",
            "stocks_sold": "SBER (50 шт) с прибылью",
            "dividends_received": "935 руб от SBER"
        },
        "tax_calculation": {
            "total_income": float(result.total_income),
            "total_expenses": float(result.total_expenses),
            "taxable_income": float(result.taxable_income),
            "ndfl_amount": float(result.ndfl_amount),
            "stock_pnl": float(result.stock_pnl),
            "dividend_income": float(result.dividend_income),
            "recommendations": result.recommendations[:3]  # Показываем только первые 3
        },
        "calculated_at": datetime.now().isoformat()
    }


@router.get("/tax-deadlines")
async def get_tax_deadlines():
    """
    Получить важные налоговые даты и сроки для текущего года.
    """
    
    current_year = datetime.now().year
    
    return {
        "tax_year": current_year - 1,  # Декларируем доходы прошлого года
        "declaration_deadline": f"31.03.{current_year}",
        "payment_deadline": f"15.07.{current_year}",
        "iis_deposit_deadline": f"31.12.{current_year}",
        "ldv_minimum_period": "3 года",
        "reminders": [
            f"Декларация о доходах {current_year - 1} года подается до 31 марта {current_year}",
            f"НДФЛ доплачивается до 15 июля {current_year}",
            f"Для получения вычета по ИИС взнос нужно сделать до 31 декабря {current_year}",
            "Льгота ЛДВ действует при владении российскими ЦБ более 3 лет"
        ]
    }


@router.get("/tax-rates")
async def get_current_tax_rates():
    """
    Получить актуальные налоговые ставки и лимиты.
    """
    
    return {
        "ndfl_rates": {
            "residents": "13%",
            "non_residents": "30%"
        },
        "iis_limits": {
            "max_annual_deposit": "1,000,000 руб",
            "max_annual_deduction": "400,000 руб (52,000 руб к возврату)",
            "minimum_holding_period": "3 года"
        },
        "ldv_limits": {
            "minimum_holding_period": "3 года",
            "max_exemption_per_year": "3,000,000 руб",
            "eligible_securities": "Российские акции и облигации"
        },
        "loss_carryover": {
            "period": "до 10 лет",
            "scope": "между различными типами операций"
        },
        "important_notes": [
            "Ставки актуальны на 2024 год",
            "Для нерезидентов действуют особые правила",
            "При смене резидентства консультируйтесь с налоговыми консультантами"
        ]
    }


@router.get("/health")
async def health_check():
    """Проверка работоспособности налогового модуля."""
    
    try:
        # Простой тест калькулятора
        calculator = TaxCalculatorRF()
        
        # Тестовые данные
        test_transactions = []
        test_portfolios = []
        
        result = calculator.calculate_taxes(
            transactions=test_transactions,
            portfolios=test_portfolios,
            tax_year=2024
        )
        
        return {
            "status": "healthy",
            "calculator_initialized": True,
            "test_calculation_completed": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
