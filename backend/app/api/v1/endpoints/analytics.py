"""Эндпоинты аналитики."""

from typing import Optional
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.core.database_sync import get_db
from app.models.user import User
from app.repositories.portfolio import PortfolioRepository
from app.repositories.transaction import TransactionRepository
from app.services.portfolio_analytics import (
    PortfolioAnalyticsService, 
    CashFlow, 
    PricePoint
)

router = APIRouter()


@router.get("/performance")
async def get_performance(
    portfolio_id: int,
    period: Optional[str] = Query(None, description="1d, 1w, 1m, 3m, 6m, 1y, 3y, 5y, inception"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение метрик производительности портфеля."""
    
    # Проверяем доступ к портфелю
    portfolio_repo = PortfolioRepository(db)
    portfolio = portfolio_repo.get_by_id(portfolio_id)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Портфель не найден"
        )
    
    if portfolio.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому портфелю"
        )
    
    # Получаем исторические данные портфеля
    end_date = datetime.now().date()
    
    if period:
        period_mapping = {
            '1d': 1,
            '1w': 7,
            '1m': 30,
            '3m': 90,
            '6m': 180,
            '1y': 365,
            '3y': 365 * 3,
            '5y': 365 * 5,
        }
        
        if period == 'inception':
            start_date = portfolio.created_at.date()
        elif period in period_mapping:
            start_date = end_date - timedelta(days=period_mapping[period])
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неподдерживаемый период"
            )
    else:
        start_date = portfolio.created_at.date()
    
    # Получаем снимки портфеля для расчета TWR
    snapshots = portfolio_repo.get_snapshots(
        portfolio_id=portfolio_id,
        start_date=datetime.combine(start_date, datetime.min.time()),
        end_date=datetime.combine(end_date, datetime.max.time())
    )
    
    if not snapshots:
        # Если нет снимков, возвращаем базовые метрики из портфеля
        return {
            "portfolio_id": portfolio_id,
            "period": period or "inception",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "twr": float(portfolio.twr_1y or 0),
            "xirr": float(portfolio.xirr or 0),
            "total_return": float(portfolio.total_pnl_percent or 0),
            "volatility": float(portfolio.volatility or 0),
            "sharpe_ratio": float(portfolio.sharpe_ratio or 0),
            "max_drawdown": float(portfolio.max_drawdown or 0),
            "calculated_at": portfolio.metrics_calculated_at.isoformat() if portfolio.metrics_calculated_at else None
        }
    
    # Конвертируем снимки в точки цен
    price_points = [
        PricePoint(date=s.snapshot_date.date(), value=s.total_value)
        for s in snapshots
    ]
    
    # Получаем денежные потоки
    transaction_repo = TransactionRepository(db)
    transactions = transaction_repo.get_portfolio_cashflows(
        portfolio_id=portfolio_id,
        start_date=datetime.combine(start_date, datetime.min.time()),
        end_date=datetime.combine(end_date, datetime.max.time())
    )
    
    cash_flows = []
    for tx in transactions:
        # Вклады считаем отрицательными (отток денег от инвестора)
        # Выводы считаем положительными (приток денег к инвестору)
        amount = tx.gross
        if tx.transaction_type.value in ['deposit', 'buy']:
            amount = -amount
        elif tx.transaction_type.value in ['dividend', 'coupon', 'withdrawal', 'sell']:
            amount = amount
            
        cash_flows.append(
            CashFlow(
                date=tx.ts.date(),
                amount=amount,
                description=f"{tx.transaction_type.value}: {amount}"
            )
        )
    
    # Рассчитываем метрики
    analytics_service = PortfolioAnalyticsService()
    
    # TWR для указанного периода
    period_days = (end_date - start_date).days
    twr = analytics_service.calculate_twr(price_points, cash_flows, period_days)
    
    # XIRR
    xirr = analytics_service.calculate_xirr(cash_flows)
    
    # Другие метрики
    volatility = analytics_service.calculate_volatility(price_points)
    max_drawdown = analytics_service.calculate_max_drawdown(price_points)
    
    # Коэффициент Шарпа
    sharpe_ratio = None
    if twr and volatility:
        sharpe_ratio = analytics_service.calculate_sharpe_ratio(twr, volatility)
    
    # Общая доходность
    total_return = None
    if len(price_points) >= 2:
        initial_value = price_points[0].value
        final_value = price_points[-1].value
        if initial_value > 0:
            total_return = ((final_value - initial_value) / initial_value) * 100
    
    return {
        "portfolio_id": portfolio_id,
        "period": period or "inception",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "twr": float(twr) if twr else None,
        "xirr": float(xirr) if xirr else None,
        "total_return": float(total_return) if total_return else None,
        "volatility": float(volatility) if volatility else None,
        "sharpe_ratio": float(sharpe_ratio) if sharpe_ratio else None,
        "max_drawdown": float(max_drawdown) if max_drawdown else None,
        "data_points": len(price_points),
        "calculated_at": datetime.now().isoformat()
    }


@router.get("/allocation")
async def get_allocation(
    portfolio_id: int,
    by: str = Query("asset_class", description="asset_class, sector, country, currency"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение распределения активов портфеля."""
    
    # Проверяем доступ к портфелю
    portfolio_repo = PortfolioRepository(db)
    portfolio = portfolio_repo.get_by_id(portfolio_id)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Портфель не найден"
        )
    
    if portfolio.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому портфелю"
        )
    
    # Получаем холдинги портфеля
    from app.repositories.account import AccountRepository
    from app.models.holding import Holding
    from app.models.instrument import Instrument
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select, and_
    
    account_repo = AccountRepository(db)
    accounts = account_repo.get_portfolio_accounts(portfolio_id)
    
    if not accounts:
        return {
            "portfolio_id": portfolio_id,
            "allocation_by": by,
            "total_value": 0,
            "allocation": {},
            "calculated_at": datetime.now().isoformat()
        }
    
    # Получаем все холдинги с инструментами
    account_ids = [acc.id for acc in accounts]
    holdings_stmt = (
        select(Holding)
        .options(selectinload(Holding.instrument))
        .where(Holding.account_id.in_(account_ids))
    )
    
    holdings_result = db.execute(holdings_stmt)
    holdings = holdings_result.scalars().all()
    
    # Преобразуем в формат для аналитики
    holdings_data = []
    for holding in holdings:
        market_value = holding.quantity * holding.avg_price  # Упрощенно, без текущих цен
        
        instrument_data = {
            'market_value': float(market_value),
            'instrument_type': holding.instrument.instrument_type.value if holding.instrument else 'unknown',
            'sector': holding.instrument.sector if holding.instrument else 'unknown',
            'country': holding.instrument.country if holding.instrument else 'unknown', 
            'currency': holding.currency,
        }
        holdings_data.append(instrument_data)
    
    # Рассчитываем распределение
    analytics_service = PortfolioAnalyticsService()
    allocation = analytics_service.calculate_asset_allocation(holdings_data)
    
    # Выбираем нужное распределение
    allocation_key_mapping = {
        'asset_class': 'by_asset_class',
        'sector': 'by_sector', 
        'country': 'by_country',
        'currency': 'by_currency'
    }
    
    if by not in allocation_key_mapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поддерживаемые типы распределения: asset_class, sector, country, currency"
        )
    
    selected_allocation = allocation.get(allocation_key_mapping[by], {})
    
    # Конвертируем Decimal в float
    formatted_allocation = {
        k: float(v) for k, v in selected_allocation.items()
    }
    
    total_value = sum(h['market_value'] for h in holdings_data)
    
    return {
        "portfolio_id": portfolio_id,
        "allocation_by": by,
        "total_value": total_value,
        "allocation": formatted_allocation,
        "calculated_at": datetime.now().isoformat()
    }


@router.get("/pnl-breakdown")
async def get_pnl_breakdown(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение детализации прибылей и убытков."""
    
    # Проверяем доступ к портфелю
    portfolio_repo = PortfolioRepository(db)
    portfolio = portfolio_repo.get_by_id(portfolio_id)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Портфель не найден"
        )
    
    if portfolio.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому портфелю"
        )
    
    # Упрощенная реализация - возвращаем данные из портфеля
    return {
        "portfolio_id": portfolio_id,
        "total_pnl": float(portfolio.total_pnl or 0),
        "total_pnl_percent": float(portfolio.total_pnl_percent or 0),
        "realized_pnl": 0,  # TODO: Рассчитать из закрытых позиций
        "unrealized_pnl": float(portfolio.total_pnl or 0),  # Упрощение
        "dividends_received": 0,  # TODO: Рассчитать из транзакций
        "fees_paid": 0,  # TODO: Рассчитать из транзакций
        "taxes_paid": 0,  # TODO: Рассчитать из транзакций
        "currency_impact": 0,  # TODO: Рассчитать валютное влияние
        "calculated_at": datetime.now().isoformat()
    }


@router.get("/top-positions")
async def get_top_positions(
    portfolio_id: int,
    limit: int = Query(10, description="Количество топ позиций"),
    sort_by: str = Query("value", description="value, pnl_percent, weight"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение топ позиций портфеля."""
    
    # Проверяем доступ к портфелю
    portfolio_repo = PortfolioRepository(db)
    portfolio = portfolio_repo.get_by_id(portfolio_id)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Портфель не найден"
        )
    
    if portfolio.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому портфелю"
        )
    
    # Получаем холдинги с инструментами
    from app.repositories.account import AccountRepository
    from app.models.holding import Holding
    from app.models.instrument import Instrument
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    
    account_repo = AccountRepository(db)
    accounts = account_repo.get_portfolio_accounts(portfolio_id)
    
    if not accounts:
        return {
            "portfolio_id": portfolio_id,
            "positions": [],
            "calculated_at": datetime.now().isoformat()
        }
    
    account_ids = [acc.id for acc in accounts]
    holdings_stmt = (
        select(Holding)
        .options(selectinload(Holding.instrument))
        .where(Holding.account_id.in_(account_ids))
    )
    
    holdings_result = db.execute(holdings_stmt)
    holdings = holdings_result.scalars().all()
    
    # Формируем позиции
    positions = []
    total_portfolio_value = float(portfolio.total_value or 0)
    
    for holding in holdings:
        market_value = float(holding.quantity * holding.avg_price)
        cost_value = float(holding.quantity * holding.avg_price)  # Упрощение
        pnl = market_value - cost_value
        pnl_percent = (pnl / cost_value * 100) if cost_value > 0 else 0
        weight = (market_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
        
        position = {
            "instrument_id": holding.instrument_id,
            "ticker": holding.instrument.ticker if holding.instrument else "N/A",
            "name": holding.instrument.name if holding.instrument else "Unknown",
            "quantity": float(holding.quantity),
            "avg_price": float(holding.avg_price),
            "market_price": float(holding.avg_price),  # TODO: Получить текущую цену
            "market_value": market_value,
            "cost_value": cost_value,
            "pnl": pnl,
            "pnl_percent": pnl_percent,
            "weight": weight,
            "currency": holding.currency
        }
        positions.append(position)
    
    # Сортируем
    if sort_by == "value":
        positions.sort(key=lambda x: x["market_value"], reverse=True)
    elif sort_by == "pnl_percent":
        positions.sort(key=lambda x: x["pnl_percent"], reverse=True)
    elif sort_by == "weight":
        positions.sort(key=lambda x: x["weight"], reverse=True)
    
    # Ограничиваем количество
    positions = positions[:limit]
    
    return {
        "portfolio_id": portfolio_id,
        "total_positions": len(holdings),
        "showing": len(positions),
        "sorted_by": sort_by,
        "positions": positions,
        "calculated_at": datetime.now().isoformat()
    }
