"""Тесты для налогового калькулятора РФ."""

import pytest
from datetime import datetime, date
from decimal import Decimal

from app.services.tax_calculator_rf import (
    TaxCalculatorRF,
    TaxPosition,
    SecurityType,
    AccountType,
    calculate_optimal_iis_strategy,
    generate_tax_optimization_recommendations
)
from app.models.transaction import Transaction, TransactionType
from app.models.portfolio import Portfolio


class TestTaxCalculatorRF:
    """Тесты основного налогового калькулятора."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        self.calculator = TaxCalculatorRF(is_resident=True)
        
    def test_ndfl_rate_for_resident(self):
        """Тест ставки НДФЛ для резидента."""
        assert self.calculator.ndfl_rate == Decimal("0.13")
        
    def test_ndfl_rate_for_nonresident(self):
        """Тест ставки НДФЛ для нерезидента."""
        nonresident_calculator = TaxCalculatorRF(is_resident=False)
        assert nonresident_calculator.ndfl_rate == Decimal("0.30")
    
    def test_stock_pnl_calculation_simple_profit(self):
        """Тест расчета прибыли по акциям - простая прибыль."""
        transactions = [
            self._create_transaction(
                symbol="SBER",
                transaction_type=TransactionType.BUY,
                quantity=Decimal("100"),
                price=Decimal("250"),
                date=datetime(2024, 1, 15)
            ),
            self._create_transaction(
                symbol="SBER", 
                transaction_type=TransactionType.SELL,
                quantity=Decimal("100"),
                price=Decimal("300"),
                date=datetime(2024, 6, 15)
            )
        ]
        
        result = self.calculator._calculate_stock_pnl(transactions)
        # Прибыль: (300 - 250) * 100 = 5000
        expected_profit = Decimal("5000")
        assert result == expected_profit
    
    def test_stock_pnl_calculation_with_commission(self):
        """Тест расчета прибыли с учетом комиссий."""
        transactions = [
            self._create_transaction(
                symbol="GAZP",
                transaction_type=TransactionType.BUY,
                quantity=Decimal("50"),
                price=Decimal("180"),
                commission=Decimal("18"),
                date=datetime(2024, 2, 10)
            ),
            self._create_transaction(
                symbol="GAZP",
                transaction_type=TransactionType.SELL,
                quantity=Decimal("50"),
                price=Decimal("200"),
                commission=Decimal("20"),
                date=datetime(2024, 8, 10)
            )
        ]
        
        result = self.calculator._calculate_stock_pnl(transactions)
        # Прибыль: (200 - 180) * 50 - 18 - 20 = 1000 - 38 = 962
        expected_profit = Decimal("962")
        assert result == expected_profit
    
    def test_stock_pnl_fifo_calculation(self):
        """Тест FIFO расчета при множественных покупках и продажах."""
        transactions = [
            # Первая покупка
            self._create_transaction(
                symbol="LKOH",
                transaction_type=TransactionType.BUY,
                quantity=Decimal("10"),
                price=Decimal("5000"),
                date=datetime(2024, 1, 10)
            ),
            # Вторая покупка по более высокой цене
            self._create_transaction(
                symbol="LKOH",
                transaction_type=TransactionType.BUY,
                quantity=Decimal("10"),
                price=Decimal("5500"),
                date=datetime(2024, 3, 10)
            ),
            # Продажа части (должна закрыть первую покупку по FIFO)
            self._create_transaction(
                symbol="LKOH",
                transaction_type=TransactionType.SELL,
                quantity=Decimal("10"),
                price=Decimal("6000"),
                date=datetime(2024, 6, 10)
            )
        ]
        
        result = self.calculator._calculate_stock_pnl(transactions)
        # По FIFO закрывается первая покупка: (6000 - 5000) * 10 = 10000
        expected_profit = Decimal("10000")
        assert result == expected_profit
    
    def test_dividend_income_calculation(self):
        """Тест расчета дивидендов."""
        transactions = [
            self._create_transaction(
                symbol="SBER",
                transaction_type=TransactionType.DIVIDEND,
                quantity=Decimal("100"),
                price=Decimal("18.70"),
                date=datetime(2024, 7, 15)
            ),
            self._create_transaction(
                symbol="GAZP",
                transaction_type=TransactionType.DIVIDEND,
                quantity=Decimal("50"),
                price=Decimal("25.50"),
                date=datetime(2024, 8, 20)
            )
        ]
        
        result = self.calculator._calculate_dividend_income(transactions)
        # Дивиденды: 100*18.70 + 50*25.50 = 1870 + 1275 = 3145
        expected_dividends = Decimal("3145")
        assert result == expected_dividends
    
    def test_full_tax_calculation(self):
        """Тест полного расчета налогов."""
        transactions = [
            # Покупка и продажа с прибылью
            self._create_transaction(
                symbol="SBER",
                transaction_type=TransactionType.BUY,
                quantity=Decimal("100"),
                price=Decimal("250"),
                date=datetime(2024, 1, 15)
            ),
            self._create_transaction(
                symbol="SBER",
                transaction_type=TransactionType.SELL,
                quantity=Decimal("100"),
                price=Decimal("300"),
                date=datetime(2024, 6, 15)
            ),
            # Дивиденды
            self._create_transaction(
                symbol="SBER",
                transaction_type=TransactionType.DIVIDEND,
                quantity=Decimal("100"),
                price=Decimal("15"),
                date=datetime(2024, 7, 15)
            )
        ]
        
        result = self.calculator.calculate_taxes(
            transactions=transactions,
            portfolios=[],
            tax_year=2024
        )
        
        # Общий доход: прибыль 5000 + дивиденды 1500 = 6500
        assert result.total_income == Decimal("6500")
        
        # НДФЛ: 6500 * 13% = 845
        expected_ndfl = Decimal("845")
        assert result.ndfl_amount == expected_ndfl
        
        # Проверяем детализацию
        assert result.stock_pnl == Decimal("5000")
        assert result.dividend_income == Decimal("1500")
    
    def test_security_type_detection(self):
        """Тест определения типа ценной бумаги."""
        assert self.calculator._get_security_type("SBER") == SecurityType.STOCK
        assert self.calculator._get_security_type("SU26238RMFS4") == SecurityType.BOND  # ОФЗ
        assert self.calculator._get_security_type("TMOS-ETF") == SecurityType.ETF
        assert self.calculator._get_security_type("RUSS-REIT") == SecurityType.REIT
    
    def test_loss_offset(self):
        """Тест зачета убытков против прибыли."""
        transactions = [
            # Прибыльная сделка
            self._create_transaction("SBER", TransactionType.BUY, Decimal("100"), Decimal("250"), datetime(2024, 1, 15)),
            self._create_transaction("SBER", TransactionType.SELL, Decimal("100"), Decimal("300"), datetime(2024, 3, 15)),
            
            # Убыточная сделка
            self._create_transaction("GAZP", TransactionType.BUY, Decimal("50"), Decimal("200"), datetime(2024, 2, 10)),
            self._create_transaction("GAZP", TransactionType.SELL, Decimal("50"), Decimal("150"), datetime(2024, 4, 10))
        ]
        
        result = self.calculator.calculate_taxes(transactions, [], 2024)
        
        # SBER прибыль: 5000, GAZP убыток: -2500
        # Общий доход: 2500
        # НДФЛ: 2500 * 13% = 325
        assert result.total_income == Decimal("2500")
        assert result.ndfl_amount == Decimal("325")
    
    def _create_transaction(
        self, 
        symbol: str, 
        transaction_type: TransactionType, 
        quantity: Decimal, 
        price: Decimal, 
        date: datetime,
        commission: Decimal = Decimal("0")
    ) -> Transaction:
        """Создать тестовую транзакцию."""
        transaction = Transaction()
        transaction.symbol = symbol
        transaction.transaction_type = transaction_type
        transaction.quantity = quantity
        transaction.price = price
        transaction.total_amount = quantity * price
        transaction.commission = commission
        transaction.currency = "RUB"
        transaction.executed_at = date
        transaction.date = date.date()
        
        # Добавляем type для совместимости со старым кодом
        transaction.type = transaction_type.value
        transaction.amount = transaction.total_amount
        
        return transaction


class TestIISStrategyCalculator:
    """Тесты калькулятора стратегии ИИС."""
    
    def test_iis_type_a_calculation(self):
        """Тест расчета ИИС типа А."""
        result = calculate_optimal_iis_strategy(
            annual_income=Decimal("2000000"),  # 2 млн руб
            expected_portfolio_return=Decimal("0.10"),  # 10%
            investment_horizon_years=5,
            annual_contribution=Decimal("400000")  # 400 тыс руб
        )
        
        # Проверяем, что результат содержит все необходимые поля
        assert "type_a_net_result" in result
        assert "type_b_net_result" in result
        assert "optimal_strategy" in result
        assert "advantage_amount" in result
        
        # Проверяем, что вычет по типу А рассчитан корректно
        expected_annual_deduction = Decimal("52000")  # 400,000 * 13%
        assert result["type_a_deductions"] == expected_annual_deduction * 5
    
    def test_iis_type_b_vs_type_a(self):
        """Тест сравнения типов ИИС."""
        # Для высокой доходности тип Б должен быть выгоднее
        high_return_result = calculate_optimal_iis_strategy(
            annual_income=Decimal("2000000"),
            expected_portfolio_return=Decimal("0.20"),  # 20% - высокая доходность
            investment_horizon_years=10,
            annual_contribution=Decimal("400000")
        )
        
        # Для низкой доходности тип А должен быть выгоднее
        low_return_result = calculate_optimal_iis_strategy(
            annual_income=Decimal("2000000"),
            expected_portfolio_return=Decimal("0.05"),  # 5% - низкая доходность
            investment_horizon_years=5,
            annual_contribution=Decimal("400000")
        )
        
        # При высокой доходности выгоднее тип Б (освобождение от НДФЛ)
        assert high_return_result["optimal_strategy"] == "B"
        
        # При низкой доходности выгоднее тип А (вычет на взносы)
        assert low_return_result["optimal_strategy"] == "A"


class TestTaxOptimizationRecommendations:
    """Тесты генерации рекомендаций по налоговой оптимизации."""
    
    def test_loss_harvesting_recommendation(self):
        """Тест рекомендации по реализации убытков."""
        from app.services.tax_calculator_rf import TaxCalculationResult
        
        # Создаем результат с налогом к доплате
        tax_result = TaxCalculationResult(
            total_income=Decimal("100000"),
            total_expenses=Decimal("5000"),
            taxable_income=Decimal("95000"),
            ndfl_base=Decimal("95000"),
            ndfl_amount=Decimal("12350"),  # 95000 * 13%
            ndfl_rate=Decimal("0.13"),
            ldv_exemption=Decimal("0"),
            iis_deduction=Decimal("0"),
            loss_carryover=Decimal("0"),
            stock_pnl=Decimal("80000"),
            bond_pnl=Decimal("15000"),
            dividend_income=Decimal("5000"),
            coupon_income=Decimal("0"),
            positions=[],
            recommendations=[]
        )
        
        # Создаем убыточные позиции
        losing_positions = [
            TaxPosition(
                symbol="GAZP",
                security_type=SecurityType.STOCK,
                account_type=AccountType.REGULAR,
                quantity=Decimal("100"),
                average_price=Decimal("200"),
                purchase_date=date(2024, 1, 15),
                unrealized_pnl=Decimal("-5000")  # Убыток 5000
            ),
            TaxPosition(
                symbol="LKOH",
                security_type=SecurityType.STOCK,
                account_type=AccountType.REGULAR,
                quantity=Decimal("50"),
                average_price=Decimal("6000"),
                purchase_date=date(2024, 2, 10),
                unrealized_pnl=Decimal("-10000")  # Убыток 10000
            )
        ]
        
        recommendations = generate_tax_optimization_recommendations(
            result=tax_result,
            current_positions=losing_positions
        )
        
        # Должна быть рекомендация по реализации убытков
        loss_harvesting_recs = [r for r in recommendations if r["type"] == "loss_harvesting"]
        assert len(loss_harvesting_recs) > 0
        
        rec = loss_harvesting_recs[0]
        assert rec["priority"] == "high"
        assert "potential_savings" in rec
    
    def test_ldv_planning_recommendation(self):
        """Тест рекомендации по планированию ЛДВ."""
        from app.services.tax_calculator_rf import TaxCalculationResult
        
        tax_result = TaxCalculationResult(
            total_income=Decimal("50000"),
            total_expenses=Decimal("2000"),
            taxable_income=Decimal("48000"),
            ndfl_base=Decimal("48000"),
            ndfl_amount=Decimal("6240"),
            ndfl_rate=Decimal("0.13"),
            ldv_exemption=Decimal("0"),
            iis_deduction=Decimal("0"),
            loss_carryover=Decimal("0"),
            stock_pnl=Decimal("48000"),
            bond_pnl=Decimal("0"),
            dividend_income=Decimal("0"),
            coupon_income=Decimal("0"),
            positions=[],
            recommendations=[]
        )
        
        # Позиция близкая к получению ЛДВ (2.8 лет держания)
        near_ldv_positions = [
            TaxPosition(
                symbol="SBER",
                security_type=SecurityType.STOCK,
                account_type=AccountType.REGULAR,
                quantity=Decimal("200"),
                average_price=Decimal("250"),
                purchase_date=date(2021, 8, 15),  # ~2.8 лет назад от условной даты теста
                unrealized_pnl=Decimal("25000")  # Прибыль 25000
            )
        ]
        
        recommendations = generate_tax_optimization_recommendations(
            result=tax_result,
            current_positions=near_ldv_positions
        )
        
        # Должна быть рекомендация по планированию ЛДВ
        ldv_recs = [r for r in recommendations if r["type"] == "ldv_planning"]
        assert len(ldv_recs) > 0
        
        rec = ldv_recs[0]
        assert rec["priority"] == "medium"
        assert "details" in rec
    
    def test_iis_opening_recommendation(self):
        """Тест рекомендации по открытию ИИС."""
        from app.services.tax_calculator_rf import TaxCalculationResult
        
        # Результат без вычета по ИИС
        tax_result = TaxCalculationResult(
            total_income=Decimal("100000"),
            total_expenses=Decimal("0"),
            taxable_income=Decimal("100000"),
            ndfl_base=Decimal("100000"),
            ndfl_amount=Decimal("13000"),
            ndfl_rate=Decimal("0.13"),
            ldv_exemption=Decimal("0"),
            iis_deduction=Decimal("0"),  # Нет вычета по ИИС
            loss_carryover=Decimal("0"),
            stock_pnl=Decimal("100000"),
            bond_pnl=Decimal("0"),
            dividend_income=Decimal("0"),
            coupon_income=Decimal("0"),
            positions=[],
            recommendations=[]
        )
        
        recommendations = generate_tax_optimization_recommendations(
            result=tax_result,
            current_positions=[]
        )
        
        # Должна быть рекомендация по открытию ИИС
        iis_recs = [r for r in recommendations if r["type"] == "iis_opening"]
        assert len(iis_recs) > 0
        
        rec = iis_recs[0]
        assert rec["priority"] == "high"
        assert rec["potential_savings"] == "52000"  # Максимальный вычет


@pytest.fixture
def sample_transactions():
    """Фикстура с примерами транзакций для тестов."""
    return [
        # Покупка SBER
        Transaction(
            symbol="SBER",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("100"),
            price=Decimal("250"),
            total_amount=Decimal("25000"),
            commission=Decimal("25"),
            currency="RUB",
            executed_at=datetime(2024, 1, 15)
        ),
        # Продажа SBER с прибылью
        Transaction(
            symbol="SBER",
            transaction_type=TransactionType.SELL,
            quantity=Decimal("50"),
            price=Decimal("300"),
            total_amount=Decimal("15000"),
            commission=Decimal("30"),
            currency="RUB",
            executed_at=datetime(2024, 6, 15)
        ),
        # Дивиденды от SBER
        Transaction(
            symbol="SBER",
            transaction_type=TransactionType.DIVIDEND,
            quantity=Decimal("50"),
            price=Decimal("18.70"),
            total_amount=Decimal("935"),
            commission=Decimal("0"),
            currency="RUB",
            executed_at=datetime(2024, 7, 15)
        )
    ]


def test_integration_full_calculation(sample_transactions):
    """Интеграционный тест полного расчета налогов."""
    calculator = TaxCalculatorRF(is_resident=True)
    
    result = calculator.calculate_taxes(
        transactions=sample_transactions,
        portfolios=[],
        tax_year=2024
    )
    
    # Проверяем основные показатели
    assert result.total_income > 0
    assert result.ndfl_amount >= 0
    assert result.ndfl_rate == Decimal("0.13")
    assert len(result.recommendations) > 0
    
    # Проверяем, что есть детализация
    assert result.stock_pnl >= 0
    assert result.dividend_income >= 0
