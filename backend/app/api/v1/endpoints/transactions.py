"""Эндпоинты для работы с транзакциями."""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.security import get_current_user
from app.core.database_sync import get_db
from app.models.user import User
from app.models.transaction import TransactionType
from app.repositories.transaction import TransactionRepository
from app.repositories.portfolio import PortfolioRepository
from app.services.import_service import ImportService

router = APIRouter()


class TransactionCreate(BaseModel):
    account_id: int
    instrument_id: Optional[int] = None
    ts: datetime
    transaction_type: TransactionType
    quantity: Optional[float] = None
    price: Optional[float] = None
    gross: float
    fee: Optional[float] = None
    tax: Optional[float] = None
    currency: str = "RUB"
    fx_rate: Optional[float] = None
    meta: Optional[str] = None


class TransactionResponse(BaseModel):
    id: int
    account_id: int
    instrument_id: Optional[int]
    ts: str
    transaction_type: str
    quantity: Optional[float]
    price: Optional[float]
    gross: float
    fee: Optional[float]
    tax: Optional[float]
    currency: str
    fx_rate: Optional[float]
    created_at: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[TransactionResponse])
async def get_transactions(
    account_id: Optional[int] = None,
    portfolio_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    transaction_type: Optional[TransactionType] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка транзакций с фильтрами."""
    transaction_repo = TransactionRepository(db)
    
    if account_id:
        # Проверяем доступ к счету через портфель
        from app.repositories.account import AccountRepository
        account_repo = AccountRepository(db)
        account = account_repo.get_by_id(account_id)
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Счет не найден"
            )
        
        # Проверяем, что счет принадлежит пользователю
        portfolio_repo = PortfolioRepository(db)
        portfolio = portfolio_repo.get_by_id(account.portfolio_id)
        
        if not portfolio or portfolio.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет доступа к этому счету"
            )
        
        # Получаем транзакции счета
        transaction_types = [transaction_type] if transaction_type else None
        transactions = transaction_repo.get_account_transactions(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            transaction_types=transaction_types,
            limit=limit,
            offset=offset
        )
    
    elif portfolio_id:
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
        
        # Получаем транзакции портфеля
        transactions = transaction_repo.get_portfolio_transactions(
            portfolio_id=portfolio_id,
            start_date=start_date,
            end_date=end_date
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать account_id или portfolio_id"
        )
    
    return [
        TransactionResponse(
            id=t.id,
            account_id=t.account_id,
            instrument_id=t.instrument_id,
            ts=t.ts.isoformat(),
            transaction_type=t.transaction_type.value,
            quantity=float(t.quantity) if t.quantity else None,
            price=float(t.price) if t.price else None,
            gross=float(t.gross),
            fee=float(t.fee) if t.fee else None,
            tax=float(t.tax) if t.tax else None,
            currency=t.currency,
            fx_rate=float(t.fx_rate) if t.fx_rate else None,
            created_at=t.created_at.isoformat()
        )
        for t in transactions
    ]


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание новой транзакции."""
    # Проверяем доступ к счету
    from app.repositories.account import AccountRepository
    account_repo = AccountRepository(db)
    account = account_repo.get_by_id(transaction_data.account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Счет не найден"
        )
    
    # Проверяем, что счет принадлежит пользователю
    portfolio_repo = PortfolioRepository(db)
    portfolio = await portfolio_repo.get_by_id(account.portfolio_id)
    
    if not portfolio or portfolio.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому счету"
        )
    
    # Создаем транзакцию
    transaction_repo = TransactionRepository(db)
    transaction = transaction_repo.create(
        account_id=transaction_data.account_id,
        instrument_id=transaction_data.instrument_id,
        ts=transaction_data.ts,
        transaction_type=transaction_data.transaction_type,
        quantity=transaction_data.quantity,
        price=transaction_data.price,
        gross=transaction_data.gross,
        fee=transaction_data.fee,
        tax=transaction_data.tax,
        currency=transaction_data.currency,
        fx_rate=transaction_data.fx_rate,
        meta=transaction_data.meta
    )
    
    return TransactionResponse(
        id=transaction.id,
        account_id=transaction.account_id,
        instrument_id=transaction.instrument_id,
        ts=transaction.ts.isoformat(),
        transaction_type=transaction.transaction_type.value,
        quantity=float(transaction.quantity) if transaction.quantity else None,
        price=float(transaction.price) if transaction.price else None,
        gross=float(transaction.gross),
        fee=float(transaction.fee) if transaction.fee else None,
        tax=float(transaction.tax) if transaction.tax else None,
        currency=transaction.currency,
        fx_rate=float(transaction.fx_rate) if transaction.fx_rate else None,
        created_at=transaction.created_at.isoformat()
    )


@router.post("/bulk")
async def bulk_create_transactions(
    transactions_data: List[TransactionCreate],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Массовое создание транзакций."""
    # Проверяем доступ ко всем счетам
    account_ids = list(set(t.account_id for t in transactions_data))
    
    from app.repositories.account import AccountRepository
    account_repo = AccountRepository(db)
    portfolio_repo = PortfolioRepository(db)
    
    for account_id in account_ids:
        account = account_repo.get_by_id(account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Счет {account_id} не найден"
            )
        
        portfolio = portfolio_repo.get_by_id(account.portfolio_id)
        if not portfolio or portfolio.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Нет доступа к счету {account_id}"
            )
    
    # Создаем транзакции
    transaction_repo = TransactionRepository(db)
    transactions_dict_data = [t.dict() for t in transactions_data]
    
    transactions = transaction_repo.bulk_create(transactions_dict_data)
    
    return {
        "message": f"Создано {len(transactions)} транзакций",
        "count": len(transactions),
        "transaction_ids": [t.id for t in transactions]
    }


@router.post("/import-csv")
async def import_csv(
    account_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Импорт транзакций из CSV файла."""
    
    # Проверяем доступ к счету
    from app.repositories.account import AccountRepository
    account_repo = AccountRepository(db)
    account = account_repo.get_by_id(account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Счет не найден"
        )
    
    portfolio_repo = PortfolioRepository(db)
    portfolio = await portfolio_repo.get_by_id(account.portfolio_id)
    
    if not portfolio or portfolio.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому счету"
        )
    
    # Проверяем тип файла
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поддерживаются только CSV файлы"
        )
    
    # Читаем содержимое файла
    try:
        content = await file.read()
        csv_content = content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            csv_content = content.decode('cp1251')  # Windows-1251 для русских файлов
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось прочитать файл. Проверьте кодировку"
            )
    
    # Импортируем данные
    try:
        import_service = ImportService(db)
        result = await import_service.import_csv(
            account_id=account_id,
            csv_content=csv_content,
            filename=file.filename
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка импорта: {str(e)}"
        )


@router.get("/import-example/{broker}")
async def get_import_example(broker: str):
    """Получение примера CSV файла для указанного брокера."""
    from app.services.import_service import ImportService
    
    import_service = ImportService(None)
    example_csv = import_service.generate_example_csv(broker)
    
    if example_csv == "Неподдерживаемый формат брокера":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=example_csv
        )
    
    return {
        "broker": broker,
        "example_csv": example_csv,
        "supported_brokers": import_service.get_supported_brokers()
    }


@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение транзакции по ID."""
    transaction_repo = TransactionRepository(db)
    transaction = transaction_repo.get_by_id(transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Транзакция не найдена"
        )
    
    # Проверяем доступ через счет и портфель
    from app.repositories.account import AccountRepository
    account_repo = AccountRepository(db)
    account = account_repo.get_by_id(transaction.account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Счет не найден"
        )
    
    portfolio_repo = PortfolioRepository(db)
    portfolio = await portfolio_repo.get_by_id(account.portfolio_id)
    
    if not portfolio or portfolio.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этой транзакции"
        )
    
    return TransactionResponse(
        id=transaction.id,
        account_id=transaction.account_id,
        instrument_id=transaction.instrument_id,
        ts=transaction.ts.isoformat(),
        transaction_type=transaction.transaction_type.value,
        quantity=float(transaction.quantity) if transaction.quantity else None,
        price=float(transaction.price) if transaction.price else None,
        gross=float(transaction.gross),
        fee=float(transaction.fee) if transaction.fee else None,
        tax=float(transaction.tax) if transaction.tax else None,
        currency=transaction.currency,
        fx_rate=float(transaction.fx_rate) if transaction.fx_rate else None,
        created_at=transaction.created_at.isoformat()
    )


@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление транзакции."""
    transaction_repo = TransactionRepository(db)
    transaction = transaction_repo.get_by_id(transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Транзакция не найдена"
        )
    
    # Проверяем доступ
    from app.repositories.account import AccountRepository
    account_repo = AccountRepository(db)
    account = account_repo.get_by_id(transaction.account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Счет не найден"
        )
    
    portfolio_repo = PortfolioRepository(db)
    portfolio = await portfolio_repo.get_by_id(account.portfolio_id)
    
    if not portfolio or portfolio.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этой транзакции"
        )
    
    # Удаляем транзакцию
    success = transaction_repo.delete(transaction_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка удаления транзакции"
        )
    
    return {"message": "Транзакция успешно удалена"}
