"""
Модуль расчета налогов для резидентов РФ.

Рассчитывает налоговые обязательства в соответствии с НК РФ:
- НДФЛ 13% с доходов от инвестиций
- Льготы по ИИС типа А и Б
- Льгота на долгосрочное владение (ЛДВ)
- Зачет убытков между операциями
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from app.models.transaction import Transaction
from app.models.portfolio import Portfolio


class AccountType(Enum):
    """Типы счетов для налогообложения."""
    REGULAR = "regular"  # Обычный брокерский счет
    IIS_A = "iis_a"      # ИИС с вычетом на взносы
    IIS_B = "iis_b"      # ИИС с освобождением доходов


class SecurityType(Enum):
    """Типы ценных бумаг для налогообложения."""
    STOCK = "stock"           # Акции
    BOND = "bond"            # Облигации
    ETF = "etf"              # ETF
    REIT = "reit"            # REIT
    DERIVATIVE = "derivative" # Производные инструменты


@dataclass
class TaxPosition:
    """Налоговая позиция по инструменту."""
    symbol: str
    security_type: SecurityType
    account_type: AccountType
    quantity: Decimal
    average_price: Decimal
    purchase_date: date
    current_price: Optional[Decimal] = None
    realized_pnl: Decimal = Decimal("0")
    unrealized_pnl: Optional[Decimal] = None


@dataclass
class TaxCalculationResult:
    """Результат расчета налогов."""
    # Доходы и расходы
    total_income: Decimal
    total_expenses: Decimal
    taxable_income: Decimal
    
    # НДФЛ
    ndfl_base: Decimal
    ndfl_amount: Decimal
    ndfl_rate: Decimal
    
    # Льготы
    ldv_exemption: Decimal  # Льгота долгосрочного владения
    iis_deduction: Decimal  # Вычет по ИИС
    loss_carryover: Decimal # Перенос убытков
    
    # По типам операций
    stock_pnl: Decimal
    bond_pnl: Decimal
    dividend_income: Decimal
    coupon_income: Decimal
    
    # Детализация
    positions: List[TaxPosition]
    recommendations: List[str]


class TaxCalculatorRF:
    """Калькулятор налогов для резидентов РФ."""
    
    # Налоговые ставки
    NDFL_RATE = Decimal("0.13")  # 13% НДФЛ для резидентов
    NDFL_RATE_NONRESIDENT = Decimal("0.30")  # 30% для нерезидентов
    
    # Лимиты и пороги
    IIS_MAX_ANNUAL_DEPOSIT = Decimal("1000000")  # 1 млн руб в год
    IIS_MAX_DEDUCTION = Decimal("400000")        # 400 тыс руб вычет
    LDV_HOLDING_PERIOD_YEARS = 3                 # 3 года для ЛДВ
    
    def __init__(self, is_resident: bool = True):
        """
        Инициализация калькулятора.
        
        Args:
            is_resident: Является ли налогоплательщик резидентом РФ
        """
        self.is_resident = is_resident
        self.ndfl_rate = self.NDFL_RATE if is_resident else self.NDFL_RATE_NONRESIDENT
    
    def calculate_taxes(
        self,
        transactions: List[Transaction],
        portfolios: List[Portfolio],
        tax_year: int = None
    ) -> TaxCalculationResult:
        """
        Рассчитать налоги за налоговый период.
        
        Args:
            transactions: Список транзакций
            portfolios: Список портфелей
            tax_year: Налоговый год (по умолчанию текущий)
        
        Returns:
            Результат расчета налогов
        """
        if tax_year is None:
            tax_year = datetime.now().year
        
        # Фильтруем транзакции по налоговому году
        year_transactions = [
            t for t in transactions 
            if t.date.year == tax_year
        ]
        
        # Группируем по типам операций
        stock_transactions = self._filter_by_type(year_transactions, SecurityType.STOCK)
        bond_transactions = self._filter_by_type(year_transactions, SecurityType.BOND)
        
        # Рассчитываем доходы по каждому типу
        stock_pnl = self._calculate_stock_pnl(stock_transactions)
        bond_pnl = self._calculate_bond_pnl(bond_transactions)
        dividend_income = self._calculate_dividend_income(year_transactions)
        coupon_income = self._calculate_coupon_income(year_transactions)
        
        # Общие доходы и расходы
        total_income = stock_pnl + bond_pnl + dividend_income + coupon_income
        total_expenses = self._calculate_total_expenses(year_transactions)
        
        # Налогооблагаемый доход
        taxable_income = max(total_income - total_expenses, Decimal("0"))
        
        # Применяем льготы
        ldv_exemption = self._calculate_ldv_exemption(year_transactions, tax_year)
        iis_deduction = self._calculate_iis_deduction(portfolios, tax_year)
        loss_carryover = self._calculate_loss_carryover(portfolios, tax_year)
        
        # Налоговая база после льгот
        ndfl_base = max(
            taxable_income - ldv_exemption - iis_deduction - loss_carryover,
            Decimal("0")
        )
        
        # НДФЛ к доплате
        ndfl_amount = ndfl_base * self.ndfl_rate
        
        # Формируем позиции
        positions = self._build_tax_positions(year_transactions)
        
        # Рекомендации
        recommendations = self._generate_recommendations(
            portfolios, year_transactions, tax_year
        )
        
        return TaxCalculationResult(
            total_income=total_income,
            total_expenses=total_expenses,
            taxable_income=taxable_income,
            ndfl_base=ndfl_base,
            ndfl_amount=ndfl_amount,
            ndfl_rate=self.ndfl_rate,
            ldv_exemption=ldv_exemption,
            iis_deduction=iis_deduction,
            loss_carryover=loss_carryover,
            stock_pnl=stock_pnl,
            bond_pnl=bond_pnl,
            dividend_income=dividend_income,
            coupon_income=coupon_income,
            positions=positions,
            recommendations=recommendations
        )
    
    def _filter_by_type(
        self, 
        transactions: List[Transaction], 
        security_type: SecurityType
    ) -> List[Transaction]:
        """Фильтровать транзакции по типу ценной бумаги."""
        return [
            t for t in transactions
            if self._get_security_type(t.symbol) == security_type
        ]
    
    def _get_security_type(self, symbol: str) -> SecurityType:
        """Определить тип ценной бумаги по символу."""
        # Упрощенная логика - в реальности нужна база данных инструментов
        if any(x in symbol.upper() for x in ["BOND", "ОФЗ", "КОРП"]):
            return SecurityType.BOND
        elif "ETF" in symbol.upper():
            return SecurityType.ETF
        elif "REIT" in symbol.upper():
            return SecurityType.REIT
        else:
            return SecurityType.STOCK
    
    def _calculate_stock_pnl(self, transactions: List[Transaction]) -> Decimal:
        """Рассчитать прибыль/убыток по акциям методом FIFO."""
        positions = {}
        total_pnl = Decimal("0")
        
        for transaction in sorted(transactions, key=lambda x: x.date):
            symbol = transaction.symbol
            
            if symbol not in positions:
                positions[symbol] = []
            
            if transaction.type == "buy":
                # Покупка - добавляем в позицию
                positions[symbol].append({
                    "quantity": transaction.quantity,
                    "price": transaction.price,
                    "date": transaction.date,
                    "commission": transaction.commission or Decimal("0")
                })
            
            elif transaction.type == "sell":
                # Продажа - закрываем позиции FIFO
                remaining_qty = transaction.quantity
                sell_revenue = transaction.quantity * transaction.price
                sell_commission = transaction.commission or Decimal("0")
                
                while remaining_qty > 0 and positions[symbol]:
                    position = positions[symbol][0]
                    
                    if position["quantity"] <= remaining_qty:
                        # Закрываем позицию полностью
                        closed_qty = position["quantity"]
                        buy_cost = closed_qty * position["price"] + position["commission"]
                        sell_part = (closed_qty / transaction.quantity) * sell_revenue
                        sell_comm_part = (closed_qty / transaction.quantity) * sell_commission
                        
                        pnl = sell_part - buy_cost - sell_comm_part
                        total_pnl += pnl
                        
                        remaining_qty -= closed_qty
                        positions[symbol].pop(0)
                    else:
                        # Частично закрываем позицию
                        closed_qty = remaining_qty
                        buy_cost = closed_qty * position["price"]
                        buy_comm_part = (closed_qty / position["quantity"]) * position["commission"]
                        sell_part = (closed_qty / transaction.quantity) * sell_revenue
                        sell_comm_part = (closed_qty / transaction.quantity) * sell_commission
                        
                        pnl = sell_part - buy_cost - buy_comm_part - sell_comm_part
                        total_pnl += pnl
                        
                        position["quantity"] -= closed_qty
                        position["commission"] -= buy_comm_part
                        remaining_qty = Decimal("0")
        
        return total_pnl
    
    def _calculate_bond_pnl(self, transactions: List[Transaction]) -> Decimal:
        """Рассчитать прибыль/убыток по облигациям."""
        # Аналогично акциям, но с учетом НКД
        return self._calculate_stock_pnl(transactions)
    
    def _calculate_dividend_income(self, transactions: List[Transaction]) -> Decimal:
        """Рассчитать доходы от дивидендов."""
        return sum(
            t.amount for t in transactions
            if t.type == "dividend"
        )
    
    def _calculate_coupon_income(self, transactions: List[Transaction]) -> Decimal:
        """Рассчитать доходы от купонов."""
        return sum(
            t.amount for t in transactions
            if t.type == "coupon"
        )
    
    def _calculate_total_expenses(self, transactions: List[Transaction]) -> Decimal:
        """Рассчитать общие расходы (комиссии)."""
        return sum(
            t.commission or Decimal("0") for t in transactions
        )
    
    def _calculate_ldv_exemption(
        self, 
        transactions: List[Transaction], 
        tax_year: int
    ) -> Decimal:
        """
        Рассчитать льготу на долгосрочное владение (ЛДВ).
        
        Освобождение от НДФЛ при владении ценными бумагами более 3 лет.
        """
        exemption = Decimal("0")
        ldv_cutoff = date(tax_year - self.LDV_HOLDING_PERIOD_YEARS, 1, 1)
        
        # Упрощенная логика - нужна более сложная реализация с FIFO
        for transaction in transactions:
            if (transaction.type == "sell" and 
                transaction.date >= ldv_cutoff and
                self._is_eligible_for_ldv(transaction.symbol)):
                
                # Определяем долю продажи, подпадающую под ЛДВ
                ldv_amount = self._calculate_ldv_amount(transaction, ldv_cutoff)
                exemption += ldv_amount
        
        return exemption
    
    def _is_eligible_for_ldv(self, symbol: str) -> bool:
        """Проверить, подпадает ли инструмент под ЛДВ."""
        # ЛДВ применяется к российским акциям и облигациям
        security_type = self._get_security_type(symbol)
        return security_type in [SecurityType.STOCK, SecurityType.BOND]
    
    def _calculate_ldv_amount(self, transaction: Transaction, cutoff: date) -> Decimal:
        """Рассчитать сумму, подпадающую под ЛДВ."""
        # Реализация расчета ЛДВ с учетом ФИФО
        # Максимальная сумма освобождения - 3 млн руб за каждый год владения
        max_exemption_per_year = Decimal("3000000")
        
        # Определяем количество полных лет владения (минимум 3)
        holding_years = max(3, (transaction.date.year - cutoff.year))
        max_total_exemption = max_exemption_per_year * holding_years
        
        # Упрощенный расчет - берем положительный результат от продажи
        if hasattr(transaction, 'profit') and transaction.profit > 0:
            return min(transaction.profit, max_total_exemption)
        
        return Decimal("0")
    
    def _calculate_iis_deduction(
        self, 
        portfolios: List[Portfolio], 
        tax_year: int
    ) -> Decimal:
        """Рассчитать вычет по ИИС типа А."""
        iis_portfolios = [p for p in portfolios if p.account_type == AccountType.IIS_A]
        
        total_deduction = Decimal("0")
        for portfolio in iis_portfolios:
            # Сумма взносов за год (максимум 400 тыс руб)
            annual_deposits = self._get_annual_deposits(portfolio, tax_year)
            deduction = min(annual_deposits, self.IIS_MAX_DEDUCTION)
            total_deduction += deduction
        
        return total_deduction
    
    def _get_annual_deposits(self, portfolio: Portfolio, tax_year: int) -> Decimal:
        """Получить сумму взносов на ИИС за год."""
        if not hasattr(portfolio, 'transactions'):
            return Decimal("0")
            
        # Суммируем все пополнения счета за год
        annual_deposits = Decimal("0")
        for transaction in portfolio.transactions:
            if (transaction.type == "deposit" and 
                transaction.date.year == tax_year):
                annual_deposits += transaction.amount
        
        # Ограничиваем максимальной суммой взноса (1 млн руб)
        return min(annual_deposits, self.IIS_MAX_ANNUAL_DEPOSIT)
    
    def _calculate_loss_carryover(
        self, 
        portfolios: List[Portfolio], 
        tax_year: int
    ) -> Decimal:
        """Рассчитать перенос убытков с предыдущих лет."""
        # Убытки можно переносить на срок до 10 лет
        total_carryover = Decimal("0")
        
        for year in range(tax_year - 10, tax_year):
            if year > 0:
                year_loss = self._get_year_loss(portfolios, year)
                if year_loss > 0:
                    total_carryover += year_loss
        
        return total_carryover
    
    def _get_year_loss(self, portfolios: List[Portfolio], year: int) -> Decimal:
        """Получить убыток за конкретный год."""
        # Логика извлечения убытков из истории
        return Decimal("0")  # Заглушка
    
    def _build_tax_positions(self, transactions: List[Transaction]) -> List[TaxPosition]:
        """Построить список налоговых позиций."""
        positions = []
        
        # Группируем транзакции по символам
        symbols = set(t.symbol for t in transactions)
        
        for symbol in symbols:
            symbol_transactions = [t for t in transactions if t.symbol == symbol]
            
            # Рассчитываем позицию
            quantity = sum(
                t.quantity if t.type == "buy" else -t.quantity
                for t in symbol_transactions
                if t.type in ["buy", "sell"]
            )
            
            if quantity > 0:
                # Есть открытая позиция
                avg_price = self._calculate_average_price(symbol_transactions)
                purchase_date = min(t.date for t in symbol_transactions if t.type == "buy")
                
                position = TaxPosition(
                    symbol=symbol,
                    security_type=self._get_security_type(symbol),
                    account_type=AccountType.REGULAR,  # Упрощение
                    quantity=quantity,
                    average_price=avg_price,
                    purchase_date=purchase_date
                )
                positions.append(position)
        
        return positions
    
    def _calculate_average_price(self, transactions: List[Transaction]) -> Decimal:
        """Рассчитать среднюю цену покупки."""
        total_cost = Decimal("0")
        total_quantity = Decimal("0")
        
        for transaction in transactions:
            if transaction.type == "buy":
                total_cost += transaction.quantity * transaction.price
                total_quantity += transaction.quantity
        
        return total_cost / total_quantity if total_quantity > 0 else Decimal("0")
    
    def _generate_recommendations(
        self,
        portfolios: List[Portfolio],
        transactions: List[Transaction],
        tax_year: int
    ) -> List[str]:
        """Сгенерировать рекомендации по налоговой оптимизации."""
        recommendations = []
        
        # Базовые рекомендации
        recommendations.extend([
            "Рассмотрите возможность открытия ИИС для получения налоговых льгот",
            "При продаже убыточных позиций можете зачесть убытки против прибыли",
            "Подача декларации обязательна до 31 марта следующего года",
            "Уплата НДФЛ производится до 15 июля"
        ])
        
        # Рекомендации по ЛДВ
        current_date = date.today()
        for transaction in transactions:
            if transaction.type == "buy":
                holding_period = (current_date - transaction.date).days / 365.25
                if holding_period > 2.5:  # Близко к 3 годам
                    recommendations.append(
                        f"Позиция {transaction.symbol} близка к получению льготы ЛДВ "
                        f"(осталось {3 - holding_period:.1f} лет)"
                    )
        
        return recommendations


def format_tax_report(result: TaxCalculationResult) -> str:
    """Сформировать текстовый отчет по налогам."""
    report = []
    report.append("=== НАЛОГОВЫЙ ОТЧЕТ ДЛЯ РЕЗИДЕНТА РФ ===")
    report.append("")
    
    report.append("ДОХОДЫ И РАСХОДЫ:")
    report.append(f"  Общий доход: {result.total_income:,.2f} руб.")
    report.append(f"  Расходы: {result.total_expenses:,.2f} руб.")
    report.append(f"  Налогооблагаемый доход: {result.taxable_income:,.2f} руб.")
    report.append("")
    
    report.append("ЛЬГОТЫ И ВЫЧЕТЫ:")
    report.append(f"  ЛДВ (долгосрочное владение): {result.ldv_exemption:,.2f} руб.")
    report.append(f"  Вычет по ИИС: {result.iis_deduction:,.2f} руб.")
    report.append(f"  Перенос убытков: {result.loss_carryover:,.2f} руб.")
    report.append("")
    
    report.append("НДФЛ:")
    report.append(f"  Налоговая база: {result.ndfl_base:,.2f} руб.")
    report.append(f"  Ставка НДФЛ: {result.ndfl_rate:.1%}")
    report.append(f"  НДФЛ к доплате: {result.ndfl_amount:,.2f} руб.")
    report.append("")
    
    report.append("ДЕТАЛИЗАЦИЯ ПО ТИПАМ:")
    report.append(f"  Акции: {result.stock_pnl:,.2f} руб.")
    report.append(f"  Облигации: {result.bond_pnl:,.2f} руб.")
    report.append(f"  Дивиденды: {result.dividend_income:,.2f} руб.")
    report.append(f"  Купоны: {result.coupon_income:,.2f} руб.")
    report.append("")
    
    if result.recommendations:
        report.append("РЕКОМЕНДАЦИИ:")
        for i, rec in enumerate(result.recommendations, 1):
            report.append(f"  {i}. {rec}")
    
    return "\n".join(report)


def calculate_optimal_iis_strategy(
    annual_income: Decimal,
    expected_portfolio_return: Decimal,
    investment_horizon_years: int,
    annual_contribution: Decimal = Decimal("400000")
) -> Dict[str, Decimal]:
    """
    Рассчитать оптимальную стратегию ИИС (тип А или Б).
    
    Args:
        annual_income: Годовой доход для расчета НДФЛ
        expected_portfolio_return: Ожидаемая доходность портфеля (в долях)
        investment_horizon_years: Горизонт инвестирования
        annual_contribution: Годовой взнос на ИИС
        
    Returns:
        Словарь с результатами для каждого типа ИИС
    """
    
    # ИИС тип А - вычет на взносы
    annual_deduction_a = min(annual_contribution * Decimal("0.13"), Decimal("52000"))
    total_deduction_a = annual_deduction_a * investment_horizon_years
    
    # Накопленная сумма с учетом доходности
    total_invested = annual_contribution * investment_horizon_years
    portfolio_value = total_invested * (1 + expected_portfolio_return) ** investment_horizon_years
    
    # ИИС тип А: НДФЛ с прибыли при выводе
    profit_a = portfolio_value - total_invested
    ndfl_a = profit_a * Decimal("0.13")
    net_result_a = portfolio_value + total_deduction_a - ndfl_a
    
    # ИИС тип Б - освобождение от НДФЛ при выводе
    net_result_b = portfolio_value  # Без НДФЛ при выводе
    
    return {
        "type_a_net_result": net_result_a,
        "type_b_net_result": net_result_b,
        "type_a_deductions": total_deduction_a,
        "type_a_ndfl": ndfl_a,
        "type_b_ndfl": Decimal("0"),
        "optimal_strategy": "A" if net_result_a > net_result_b else "B",
        "advantage_amount": abs(net_result_a - net_result_b)
    }


def generate_tax_optimization_recommendations(
    result: TaxCalculationResult,
    current_positions: List[TaxPosition],
    market_data: Optional[Dict] = None
) -> List[Dict[str, str]]:
    """
    Генерировать персонализированные рекомендации по налоговой оптимизации.
    
    Args:
        result: Результат налогового расчета
        current_positions: Текущие позиции
        market_data: Рыночные данные (опционально)
        
    Returns:
        Список рекомендаций с приоритетами
    """
    recommendations = []
    
    # Рекомендации по реализации убытков
    losing_positions = [p for p in current_positions 
                       if p.unrealized_pnl and p.unrealized_pnl < 0]
    
    if losing_positions and result.ndfl_amount > 0:
        total_losses = sum(abs(p.unrealized_pnl) for p in losing_positions)
        potential_savings = min(total_losses, result.ndfl_base) * result.ndfl_rate
        
        recommendations.append({
            "type": "loss_harvesting",
            "priority": "high",
            "title": "Реализация налоговых убытков",
            "description": f"Продав убыточные позиции на сумму {total_losses:,.0f} руб, "
                          f"вы можете сэкономить {potential_savings:,.0f} руб НДФЛ",
            "potential_savings": str(potential_savings),
            "action_required": "Рассмотрите продажу убыточных позиций до конца года"
        })
    
    # Рекомендации по ЛДВ
    near_ldv_positions = []
    current_date = date.today()
    
    for position in current_positions:
        holding_period = (current_date - position.purchase_date).days / 365.25
        if 2.5 <= holding_period < 3:  # Близко к 3 годам
            near_ldv_positions.append({
                "symbol": position.symbol,
                "days_until_ldv": int((3 * 365.25) - (current_date - position.purchase_date).days),
                "potential_exemption": position.unrealized_pnl if position.unrealized_pnl and position.unrealized_pnl > 0 else 0
            })
    
    if near_ldv_positions:
        recommendations.append({
            "type": "ldv_planning",
            "priority": "medium",
            "title": "Планирование льготы долгосрочного владения",
            "description": f"У вас есть {len(near_ldv_positions)} позиций, близких к получению ЛДВ",
            "details": near_ldv_positions,
            "action_required": "Избегайте продажи этих позиций до получения ЛДВ"
        })
    
    # Рекомендации по ИИС
    if result.iis_deduction == 0:
        recommendations.append({
            "type": "iis_opening",
            "priority": "high",
            "title": "Открытие индивидуального инвестиционного счета",
            "description": "ИИС позволяет получить вычет до 52,000 руб/год или освобождение от НДФЛ",
            "potential_savings": "52000",
            "action_required": "Рассмотрите открытие ИИС для налоговых льгот"
        })
    
    # Рекомендации по срокам подачи декларации
    if result.ndfl_amount > 0:
        recommendations.append({
            "type": "declaration_deadline",
            "priority": "critical",
            "title": "Сроки подачи декларации и уплаты налога",
            "description": f"НДФЛ к доплате: {result.ndfl_amount:,.0f} руб",
            "action_required": "Подача декларации до 31 марта, уплата до 15 июля"
        })
    
    return sorted(recommendations, 
                 key=lambda x: {"critical": 4, "high": 3, "medium": 2, "low": 1}[x["priority"]], 
                 reverse=True)
