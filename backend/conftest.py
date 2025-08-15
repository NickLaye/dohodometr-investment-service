"""
Global test configuration and fixtures for pytest.

This file contains shared pytest fixtures that are available to all tests
in the backend test suite.
"""
import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
import builtins as _builtins

from app.core.config import settings
from app.core.database import Base, get_db
import app.models  # ensure models are imported so Base.metadata knows all tables
from app.schemas.auth import UserRegister as _UserCreate
_builtins.UserCreate = _UserCreate


# Гарантируем создание схемы и для sync-движка, который используется в тестах напрямую
@pytest.fixture(scope="session", autouse=True)
def _ensure_sync_schema_created():
    # Переопределяем sync engine на in-memory SQLite вне зависимости от SETTINGS,
    # чтобы избежать подключения к Postgres при unit-тестах
    import app.core.database_sync as dbsync
    from sqlalchemy.pool import StaticPool as _StaticPool
    from sqlalchemy import create_engine as _create_engine
    dbsync.engine = _create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=_StaticPool,
        echo=False,
    )
    import app.models as _  # noqa: F401
    dbsync.Base.metadata.create_all(bind=dbsync.engine)
    yield
    try:
        dbsync.Base.metadata.drop_all(bind=dbsync.engine)
    except Exception:
        pass
from app.core.database_sync import get_db as get_db_sync
from app.main import app


# Test database configuration
TEST_DATABASE_URL = "sqlite:///./test.db"
TEST_DATABASE_URL_ASYNC = "sqlite+aiosqlite:///./test.db"

# Configure test settings (force predictable ENV for unit tests)
os.environ.setdefault("DATABASE_URL", TEST_DATABASE_URL)
# Гарантируем, что pydantic Settings не подтянет ENVIRONMENT из .env и внешнего окружения
os.environ["ENVIRONMENT"] = "development"
# Не задаём фиксированный SECRET_KEY для тестов, чтобы тесты генерации ключей проходили
os.environ["REDIS_URL"] = "redis://localhost:6379/1"


# =============================================================================
# Session Scoped Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def engine():
    """Create test database engine (in-memory SQLite with StaticPool)."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    # Create tables
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="session")
async def async_engine():
    """Create async test database engine (in-memory)."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# =============================================================================
# Function Scoped Fixtures
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def _override_sessionlocal(engine):
    """Bind app.core.database.SessionLocal to the in-memory engine for all tests."""
    import app.core.database as dbmod
    import app.core.database_sync as dbsync
    try:
        dbmod.SessionLocal.configure(bind=engine)
    except Exception:
        pass
    try:
        dbsync.engine = engine
        dbsync.SessionLocal.configure(bind=engine)
        # Ensure tables exist for sync Base on this engine
        dbsync.Base.metadata.create_all(bind=engine)
    except Exception:
        pass

@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    
    # Create session bound to the connection
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()
    
    yield session
    
    # Cleanup
    session.close()
    transaction.rollback()
    connection.close()
    # Полный сброс состояния БД между тестами для изоляции (SQLite in-memory + StaticPool)
    try:
        import app.models as _  # noqa: F401
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
    except Exception:
        # В тестах не должен падать teardown
        pass


@pytest_asyncio.fixture
async def async_db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh async database session for each test."""
    async with async_engine.begin() as connection:
        async_session = AsyncSession(bind=connection, expire_on_commit=False)
        
        yield async_session
        
        await async_session.close()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    """Create a test client with overridden database dependency."""
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db_sync] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Cleanup
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(async_db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client with overridden database dependency."""
    
    async def override_get_db():
        try:
            yield async_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client
    
    # Cleanup
    app.dependency_overrides.clear()


# =============================================================================
# Authentication Fixtures
# =============================================================================

@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    return {
        "id": 1,
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def auth_headers(db_session: Session, mock_user):
    """Create authentication headers for testing.

    Гарантирует наличие пользователя в БД и создает валидный JWT на его ID.
    """
    from app.core.security import create_access_token
    from app.repositories.user import UserRepository
    from app.schemas.auth import UserRegister

    user_repo = UserRepository(db_session)
    existing = user_repo.get_by_email(mock_user["email"])  # type: ignore[index]
    if existing is None:
        # Создаем пользователя с безопасным паролем для тестов
        reg = UserRegister(
            email=mock_user["email"],
            username=mock_user["username"],
            password="StrongP@ssw0rd123",
            full_name=mock_user["full_name"],
        )
        existing = user_repo.create(reg)

    access_token = create_access_token(subject=existing.id)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def superuser_headers():
    """Create superuser authentication headers for testing."""
    from app.core.security import create_access_token
    
    access_token = create_access_token(subject="1", is_superuser=True)
    return {"Authorization": f"Bearer {access_token}"}


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock = MagicMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = 1
    mock.exists.return_value = False
    return mock


@pytest.fixture
def mock_celery():
    """Mock Celery task."""
    mock = MagicMock()
    mock.delay.return_value = MagicMock(id="mock-task-id")
    mock.apply_async.return_value = MagicMock(id="mock-task-id")
    return mock


@pytest.fixture
def mock_email_service():
    """Mock email service."""
    mock = AsyncMock()
    mock.send_email.return_value = True
    return mock


# =============================================================================
# Test Data Fixtures
# =============================================================================

@pytest.fixture
def sample_portfolio():
    """Sample portfolio data for testing."""
    return {
        "name": "Test Portfolio",
        "description": "A test portfolio for unit tests",
        "base_currency": "USD",
        "is_active": True,
    }


@pytest.fixture
def sample_account():
    """Sample account data for testing."""
    return {
        "name": "Test Brokerage Account",
        "account_type": "brokerage",
        "broker": "test_broker",
        "account_number": "TEST123456",
        "currency": "USD",
        "is_active": True,
    }


@pytest.fixture
def sample_transaction():
    """Sample transaction data for testing."""
    return {
        "date": "2024-01-15",
        "type": "buy",
        "symbol": "AAPL",
        "quantity": 10,
        "price": 150.00,
        "currency": "USD",
        "commission": 1.00,
        "description": "Buy Apple shares",
    }


@pytest.fixture
def sample_instrument():
    """Sample instrument data for testing."""
    return {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "type": "stock",
        "currency": "USD",
        "exchange": "NASDAQ",
        "isin": "US0378331005",
        "sector": "Technology",
        "industry": "Consumer Electronics",
    }


# =============================================================================
# File Upload Fixtures
# =============================================================================

@pytest.fixture
def sample_csv_file():
    """Sample CSV file content for testing imports."""
    csv_content = """Date,Type,Symbol,Quantity,Price,Currency,Commission
2024-01-15,Buy,AAPL,10,150.00,USD,1.00
2024-01-16,Sell,AAPL,5,155.00,USD,1.00
2024-01-17,Dividend,AAPL,10,0.25,USD,0.00"""
    
    from io import StringIO
    return StringIO(csv_content)


@pytest.fixture
def invalid_csv_file():
    """Invalid CSV file content for testing error handling."""
    csv_content = """Invalid,Header,Format
Not,A,Valid,Transaction,Row"""
    
    from io import StringIO
    return StringIO(csv_content)


# =============================================================================
# Async Utilities
# =============================================================================

@pytest.fixture
def anyio_backend():
    """Use asyncio backend for async tests."""
    return "asyncio"


# =============================================================================
# Cleanup and Teardown
# =============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Automatically cleanup test files after each test."""
    yield
    
    # Clean up test database files
    test_files = ["test.db", "test.db-wal", "test.db-shm"]
    for file in test_files:
        if os.path.exists(file):
            try:
                os.remove(file)
            except (OSError, PermissionError):
                pass  # File might be in use, ignore


# =============================================================================
# Pytest Configuration
# =============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "auth: marks tests related to authentication"
    )
    config.addinivalue_line(
        "markers", "portfolio: marks tests related to portfolio management"
    )
    config.addinivalue_line(
        "markers", "transactions: marks tests related to transactions"
    )
    config.addinivalue_line(
        "markers", "analytics: marks tests related to analytics"
    )


# =============================================================================
# Test Environment Validation
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def validate_test_environment():
    """Validate that we're running in acceptable test environment."""
    # Допустимы два значения: 'testing' (интеграционные) и 'development' (юнит-тест настройки)
    assert settings.ENVIRONMENT in ("testing", "development"), "Unexpected ENVIRONMENT for tests"
    assert ("test" in settings.DATABASE_URL.lower()) or ("sqlite" in settings.DATABASE_URL.lower()), "Tests must use test or sqlite database"
    yield
