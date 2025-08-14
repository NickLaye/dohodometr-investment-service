"""Эндпоинты для работы с портфелями."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from fastapi.responses import Response

from app.core.security import get_current_user
from app.core.database_sync import get_db
from app.models.user import User
from app.repositories.portfolio import PortfolioRepository
from app.services.portfolio_analytics import PortfolioAnalyticsService
from app.schemas.portfolio import PortfolioCreate as PortfolioCreateSchema, PortfolioUpdate as PortfolioUpdateSchema

router = APIRouter()


class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None
    base_currency: Optional[str] = None
    currency: Optional[str] = None  # alias for base_currency


class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_currency: Optional[str] = None
    currency: Optional[str] = None  # alias for base_currency


class PortfolioResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    base_currency: str
    currency: str
    is_active: bool
    total_value: Optional[float]
    total_cost: Optional[float]
    total_pnl: Optional[float]
    total_pnl_percent: Optional[float]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[PortfolioResponse])
def get_portfolios(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение списка портфелей пользователя."""
    portfolio_repo = PortfolioRepository(db)
    portfolios = portfolio_repo.get_user_portfolios(current_user.id)
    
    return [
        PortfolioResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            base_currency=p.base_currency,
            currency=p.base_currency,
            is_active=p.is_active,
            total_value=float(p.total_value) if p.total_value else None,
            total_cost=float(p.total_cost) if p.total_cost else None,
            total_pnl=float(p.total_pnl) if p.total_pnl else None,
            total_pnl_percent=float(p.total_pnl_percent) if p.total_pnl_percent else None,
            created_at=p.created_at.isoformat(),
            updated_at=p.updated_at.isoformat()
        )
        for p in portfolios
    ]


@router.post("/", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
def create_portfolio(
    portfolio_data: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создание нового портфеля."""
    portfolio_repo = PortfolioRepository(db)
    
    base_currency = portfolio_data.base_currency or portfolio_data.currency or "RUB"
    schema = PortfolioCreateSchema(
        name=portfolio_data.name,
        description=portfolio_data.description,
        base_currency=base_currency,
    )

    portfolio = portfolio_repo.create(
        schema,
        user_id=current_user.id,
    )
    
    return PortfolioResponse(
        id=portfolio.id,
        name=portfolio.name,
        description=portfolio.description,
        base_currency=portfolio.base_currency,
        currency=portfolio.base_currency,
        is_active=portfolio.is_active,
        total_value=float(portfolio.total_value) if portfolio.total_value else None,
        total_cost=float(portfolio.total_cost) if portfolio.total_cost else None,
        total_pnl=float(portfolio.total_pnl) if portfolio.total_pnl else None,
        total_pnl_percent=float(portfolio.total_pnl_percent) if portfolio.total_pnl_percent else None,
        created_at=portfolio.created_at.isoformat(),
        updated_at=portfolio.updated_at.isoformat()
    )


@router.get("/{portfolio_id}")
def get_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение портфеля по ID."""
    portfolio_repo = PortfolioRepository(db)
    portfolio = portfolio_repo.get_by_id(portfolio_id)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Портфель не найден"
        )
    
    if portfolio.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому портфелю"
        )
    
    return PortfolioResponse(
        id=portfolio.id,
        name=portfolio.name,
        description=portfolio.description,
        base_currency=portfolio.base_currency,
        currency=portfolio.base_currency,
        is_active=portfolio.is_active,
        total_value=float(portfolio.total_value) if portfolio.total_value else None,
        total_cost=float(portfolio.total_cost) if portfolio.total_cost else None,
        total_pnl=float(portfolio.total_pnl) if portfolio.total_pnl else None,
        total_pnl_percent=float(portfolio.total_pnl_percent) if portfolio.total_pnl_percent else None,
        created_at=portfolio.created_at.isoformat(),
        updated_at=portfolio.updated_at.isoformat()
    )


@router.put("/{portfolio_id}")
def update_portfolio(
    portfolio_id: int,
    portfolio_data: PortfolioUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление портфеля."""
    portfolio_repo = PortfolioRepository(db)
    portfolio = portfolio_repo.get_by_id(portfolio_id)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Портфель не найден"
        )
    
    if portfolio.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому портфелю"
        )
    
    # Собираем обновления
    update_payload = portfolio_data.dict(exclude_unset=True)
    if "currency" in update_payload and "base_currency" not in update_payload:
        update_payload["base_currency"] = update_payload.pop("currency")
    
    updated = portfolio_repo.update(portfolio_id, PortfolioUpdateSchema(**update_payload))
    
    return PortfolioResponse(
        id=updated.id,
        name=updated.name,
        description=updated.description,
        base_currency=updated.base_currency,
        currency=updated.base_currency,
        is_active=updated.is_active,
        total_value=float(updated.total_value) if updated.total_value else None,
        total_cost=float(updated.total_cost) if updated.total_cost else None,
        total_pnl=float(updated.total_pnl) if updated.total_pnl else None,
        total_pnl_percent=float(updated.total_pnl_percent) if updated.total_pnl_percent else None,
        created_at=updated.created_at.isoformat(),
        updated_at=updated.updated_at.isoformat()
    )


@router.delete("/{portfolio_id}")
def delete_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Мягкое удаление портфеля."""
    portfolio_repo = PortfolioRepository(db)
    portfolio = portfolio_repo.get_by_id(portfolio_id)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Портфель не найден"
        )
    
    if portfolio.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому портфелю"
        )
    
    success = portfolio_repo.delete(portfolio_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка удаления портфеля"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{portfolio_id}/summary")
def get_portfolio_summary(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение детальной сводки по портфелю."""
    portfolio_repo = PortfolioRepository(db)
    
    # Проверяем доступ
    portfolio = portfolio_repo.get_by_id(portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Портфель не найден"
        )
    
    if portfolio.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому портфелю"
        )
    
    # Получаем детальную сводку
    summary = portfolio_repo.get_portfolio_summary(portfolio_id)
    
    return summary
