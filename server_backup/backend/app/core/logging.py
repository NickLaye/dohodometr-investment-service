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
__all__ = ["logger", "setup_logging", "get_logger", "log_security_event"]
def log_security_event(event: str, user_id: str = None, details: Dict[str, Any] = None) -> None:
    """Логирование событий безопасности."""
    extra_info = {"user_id": user_id, "event_type": "security"}
    if details:
        extra_info.update(details)
    
    logger.info(f"Security event: {event}", extra=extra_info)
