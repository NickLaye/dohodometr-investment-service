"""
Утилита для получения Redis-клиента (необязательный компонент).

Поведение:
- Возвращает валидный redis.Redis при доступной конфигурации и успешном ping
- Возвращает None, если Redis недоступен или не сконфигурирован (не ломаем приложение)
"""

from typing import Optional

from app.core.config import settings
from app.core.logging import logger


def get_redis_client() -> Optional["redis.Redis"]:
    try:
        # Ленивая загрузка библиотеки, чтобы не требовать её в окружении тестов без Redis
        import redis  # type: ignore

        host = settings.REDIS_HOST
        port = settings.REDIS_PORT
        if not host or port is None:
            return None

        client: "redis.Redis" = redis.Redis(
            host=host,
            port=port,
            password=settings.REDIS_PASSWORD,
            db=0,
            socket_connect_timeout=2,
            socket_timeout=2,
        )

        try:
            client.ping()
            return client
        except Exception as ping_err:  # noqa: BLE001
            logger.warning(f"Redis ping failed: {ping_err}")
            return None

    except Exception as import_err:  # noqa: BLE001
        logger.debug(f"Redis library not available or misconfigured: {import_err}")
        return None


