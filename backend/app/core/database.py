"""
Настройка подключения к базе данных (sync). Делим один и тот же Base с database_sync,
чтобы тестовая и основная метадата были едины.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

from app.core.config import settings
from app.core.logging import logger
from app.core.database_sync import Base  # Используем общий Base


# Создание синхронного движка
_db_url = settings.database_url_sync
_common_kwargs = dict(echo=settings.DATABASE_ECHO, pool_pre_ping=True, pool_recycle=3600)
if _db_url.startswith("sqlite") and settings.ENVIRONMENT == "testing":
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        **_common_kwargs,
    )
else:
    engine = create_engine(_db_url, **_common_kwargs)

# Создание фабрики сессий
session_maker = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Dependency для получения сессии базы данных."""
    session = session_maker()
    try:
        yield session
    except Exception as e:
        logger.error(f"Ошибка сессии базы данных: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Инициализация базы данных."""
    try:
        # Импортируем все модели для создания таблиц
        from app.models import (
            user, portfolio, account, instrument, price, transaction,
            cashflow, benchmark, goal, alert, notification,
            broker_connection, tag, audit, custom_asset, crypto_asset
        )
        
        # Создаем таблицы
        Base.metadata.create_all(engine)
        logger.info("Таблицы базы данных созданы")
        
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        raise


def close_db() -> None:
    """Закрытие подключения к базе данных."""
    engine.dispose()
    logger.info("Подключение к базе данных закрыто")


# Функции для работы с транзакциями
class DatabaseTransaction:
    """Контекстный менеджер для работы с транзакциями."""
    
    def __init__(self, session: Session):
        self.session = session
        self.transaction = None
    
    def __aenter__(self):
        self.transaction = self.session.begin()
        return self.session
    
    def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.transaction.rollback()
            logger.error(f"Транзакция отменена из-за ошибки: {exc_val}")
        else:
            self.transaction.commit()
        return False


def execute_in_transaction(session: Session, operations):
    """Выполнение операций в транзакции."""
    with DatabaseTransaction(session) as tx_session:
        if callable(operations):
            return operations(tx_session)
        else:
            for operation in operations:
                operation(tx_session)


# Утилиты для работы с базой данных
def check_database_connection() -> bool:
    """Проверка подключения к базе данных."""
    try:
        with engine.begin() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        return False


def get_database_info() -> dict:
    """Получение информации о базе данных."""
    try:
        with engine.begin() as conn:
            result = conn.execute("""
                SELECT 
                    version() as version,
                    current_database() as database,
                    current_user as user,
                    inet_server_addr() as host,
                    inet_server_port() as port
            """)
            row = result.fetchone()
            
            return {
                "version": row[0],
                "database": row[1],
                "user": row[2],
                "host": row[3],
                "port": row[4],
                "encoding": "UTF-8",
                "timezone": settings.DEFAULT_TIMEZONE
            }
    except Exception as e:
        logger.error(f"Ошибка получения информации о БД: {e}")
        return {"error": str(e)}


# Декоратор для повторных попыток подключения
def with_db_retry(max_retries: int = 3, delay: float = 1.0):
    """Декоратор для повторных попыток операций с БД."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Попытка {attempt + 1}/{max_retries} не удалась: {e}")
                    
                    if attempt < max_retries - 1:
                        time.sleep(delay * (2 ** attempt))  # Экспоненциальная задержка
                    
            logger.error(f"Все {max_retries} попытки не удались. Последняя ошибка: {last_exception}")
            raise last_exception
        
        return wrapper
    return decorator
