"""
Настройка подключения к базе данных PostgreSQL.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.pool import NullPool
from sqlalchemy import MetaData

from app.core.config import settings
from app.core.logging import logger


# Создание асинхронного движка
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DATABASE_ECHO,
    poolclass=NullPool if settings.ENVIRONMENT == "testing" else None,
    pool_pre_ping=True,
    pool_recycle=3600,  # Переподключение каждый час
    connect_args={
        "server_settings": {
            "application_name": f"{settings.APP_NAME}-{settings.ENVIRONMENT}",
            "timezone": settings.DEFAULT_TIMEZONE,
        }
    }
)

# Создание фабрики сессий
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""
    
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s"
        }
    )
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Автоматическое именование таблиц."""
        return cls.__name__.lower()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для получения сессии базы данных."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Ошибка сессии базы данных: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Инициализация базы данных."""
    try:
        # Импортируем все модели для создания таблиц
        from app.models import (
            user, portfolio, account, instrument, price, transaction,
            cashflow, benchmark, goal, alert, notification,
            broker_connection, tag, audit, custom_asset, crypto_asset
        )
        
        async with engine.begin() as conn:
            # Создаем таблицы
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Таблицы базы данных созданы")
            
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        raise


async def close_db() -> None:
    """Закрытие подключения к базе данных."""
    await engine.dispose()
    logger.info("Подключение к базе данных закрыто")


# Функции для работы с транзакциями
class DatabaseTransaction:
    """Контекстный менеджер для работы с транзакциями."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.transaction = None
    
    async def __aenter__(self):
        self.transaction = await self.session.begin()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.transaction.rollback()
            logger.error(f"Транзакция отменена из-за ошибки: {exc_val}")
        else:
            await self.transaction.commit()
        return False


async def execute_in_transaction(session: AsyncSession, operations):
    """Выполнение операций в транзакции."""
    async with DatabaseTransaction(session) as tx_session:
        if callable(operations):
            return await operations(tx_session)
        else:
            for operation in operations:
                await operation(tx_session)


# Утилиты для работы с базой данных
async def check_database_connection() -> bool:
    """Проверка подключения к базе данных."""
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        return False


async def get_database_info() -> dict:
    """Получение информации о базе данных."""
    try:
        async with engine.begin() as conn:
            result = await conn.execute("""
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
        async def wrapper(*args, **kwargs):
            import asyncio
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Попытка {attempt + 1}/{max_retries} не удалась: {e}")
                    
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (2 ** attempt))  # Экспоненциальная задержка
                    
            logger.error(f"Все {max_retries} попытки не удались. Последняя ошибка: {last_exception}")
            raise last_exception
        
        return wrapper
    return decorator
