"""
Настройка логирования.
"""

import logging
import sys
from typing import Dict, Any

# Создаем логгер
logger = logging.getLogger("investment_service")

def setup_logging(level: str = "INFO") -> None:
    """Настройка логирования для приложения."""
    
    # Конфигурация форматирования
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Настройка корневого логгера
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Настройка логгера приложения
    logger.setLevel(getattr(logging, level.upper()))
    
    # Отключаем избыточное логирование сторонних библиотек
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """Получение именованного логгера."""
    return logging.getLogger(f"investment_service.{name}")

# Экспортируем основной логгер
__all__ = ["logger", "setup_logging", "get_logger"]