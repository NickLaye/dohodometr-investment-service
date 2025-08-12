#!/usr/bin/env python3
"""
Скрипт для проверки готовности сервисов к запуску.
"""

import asyncio
import time
import sys
import os
from typing import Dict, Any

# Добавляем текущую директорию в путь Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import psycopg2
    import redis
    import httpx
    from sqlalchemy import create_engine, text
    from app.core.config import Settings
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Установите зависимости: pip install -r requirements.txt")
    sys.exit(1)


def check_postgres(settings: Settings) -> bool:
    """Проверка подключения к PostgreSQL."""
    try:
        engine = create_engine(settings.database_url_sync)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL: {version[:50]}...")
            return True
    except Exception as e:
        print(f"❌ PostgreSQL недоступен: {e}")
        return False


def check_redis(settings: Settings) -> bool:
    """Проверка подключения к Redis."""
    try:
        r = redis.from_url(settings.REDIS_URL)
        info = r.info()
        version = info.get('redis_version', 'unknown')
        print(f"✅ Redis: version {version}")
        return True
    except Exception as e:
        print(f"❌ Redis недоступен: {e}")
        return False


async def check_minio(settings: Settings) -> bool:
    """Проверка подключения к MinIO."""
    try:
        # Простая проверка HTTP доступности
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{settings.MINIO_HOST}:{settings.MINIO_PORT}/minio/health/live",
                timeout=5.0
            )
            if response.status_code == 200:
                print("✅ MinIO: доступен")
                return True
            else:
                print(f"❌ MinIO: HTTP {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ MinIO недоступен: {e}")
        return False


def check_environment() -> Dict[str, Any]:
    """Проверка переменных окружения."""
    settings = Settings()
    
    print("🔍 Проверка конфигурации:")
    print(f"  - База данных: {settings.DATABASE_HOST}:{settings.DATABASE_PORT}")
    print(f"  - Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    print(f"  - MinIO: {settings.MINIO_HOST}:{settings.MINIO_PORT}")
    print(f"  - JWT Secret: {'✅ установлен' if settings.JWT_SECRET_KEY else '❌ не установлен'}")
    print(f"  - Debug режим: {settings.DEBUG}")
    
    return {
        "settings": settings,
        "jwt_secret_set": bool(settings.JWT_SECRET_KEY),
    }


async def main():
    """Основная функция проверки."""
    print("🚀 Проверка готовности сервисов к запуску...\n")
    
    # Проверяем конфигурацию
    env_check = check_environment()
    settings = env_check["settings"]
    
    if not env_check["jwt_secret_set"]:
        print("❌ Критическая ошибка: не установлен JWT_SECRET_KEY")
        return False
    
    print()
    
    # Проверяем сервисы
    checks = {
        "PostgreSQL": check_postgres(settings),
        "Redis": check_redis(settings),
        "MinIO": await check_minio(settings),
    }
    
    print()
    
    # Результаты
    passed = sum(checks.values())
    total = len(checks)
    
    if passed == total:
        print(f"🎉 Все проверки пройдены ({passed}/{total})!")
        print("Сервис готов к запуску.")
        return True
    else:
        print(f"⚠️  Пройдено проверок: {passed}/{total}")
        print("Некоторые сервисы недоступны. Проверьте docker-compose.")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        sys.exit(1)
