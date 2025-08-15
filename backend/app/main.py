from sqlalchemy import text
"""
Главный файл FastAPI приложения для сервиса учета инвестиций.
"""

import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app, Counter, Histogram, Gauge
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.core.config import settings
from app.core.database_sync import engine, get_db
from app.core.security import get_current_user, init_token_blacklist
from app.api.v1.api import api_router
from app.api.health import router as health_router
from app.core.logging import setup_logging, logger

# Prometheus metrics
REQUEST_COUNT = Counter(
    'investment_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)
REQUEST_DURATION = Histogram(
    'investment_api_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)
ACTIVE_CONNECTIONS = Gauge(
    'investment_api_active_connections',
    'Active connections'
)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Обработка запуска и остановки приложения."""
    # Startup
    logger.info("Запуск сервиса учета инвестиций...")
    
    # Инициализация Sentry для мониторинга ошибок
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                FastApiIntegration(auto_enabling_integrations=False),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=0.1,
            environment=settings.ENVIRONMENT,
            release=settings.APP_VERSION,
        )
        logger.info("Sentry инициализирован")
    
    # Проверка подключения к базе данных
    try:
        with engine.begin() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Подключение к базе данных установлено")
        # В тестовой среде и SQLite гарантируем наличие схемы
        try:
            if settings.ENVIRONMENT.lower() in {"testing", "development"} and str(engine.url).startswith("sqlite"):
                from app.core.database_sync import Base as SyncBase
                import app.models as _  # ensure models imported
                SyncBase.metadata.create_all(bind=engine)
        except Exception as schema_err:
            logger.warning(f"Не удалось автоинициализировать схему БД: {schema_err}")
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        raise
    
    # Инициализация Redis-блеклиста токенов (для logout/refresh rotation)
    try:
        if settings.REDIS_HOST and settings.REDIS_PORT is not None:
            import redis  # lazy import

            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=0,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            # Простая проверка соединения (не критично)
            try:
                redis_client.ping()
                init_token_blacklist(redis_client)
                logger.info("Token blacklist инициализирован (Redis)")
            except Exception as ping_err:
                logger.warning(f"Не удалось инициализировать Redis blacklist: {ping_err}")
    except Exception as e:
        # Никогда не блокируем запуск сервиса из-за Redis
        logger.warning(f"Redis недоступен или не сконфигурирован: {e}")

    logger.info("Сервис запущен и готов к работе")
    
    yield
    
    # Shutdown
    logger.info("Остановка сервиса...")
    engine.dispose()
    logger.info("Сервис остановлен")


def create_application() -> FastAPI:
    """Создание и настройка FastAPI приложения."""
    
    # Настройка логирования
    setup_logging()
    
    # Создание приложения
    app = FastAPI(
        title=settings.APP_NAME,
        description="Облачный сервис для учёта инвестиционных портфелей",
        version=settings.APP_VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )
    
    # Middleware для CORS
    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Middleware для доверенных хостов
    if settings.TRUSTED_HOSTS and settings.ENVIRONMENT.lower() != "testing":
        # Добавляем 'testserver' для совместимости с TestClient
        allowed = [str(host) for host in settings.TRUSTED_HOSTS]
        if "testserver" not in allowed:
            allowed.append("testserver")
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=allowed,
        )
    else:
        # В тестовой среде принимаем любые хосты, чтобы избежать Invalid host header
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]
        )

    # Принудительный HTTPS в prod
    if settings.ENVIRONMENT.lower() in {"production", "staging"}:
        app.add_middleware(HTTPSRedirectMiddleware)
    
    # Rate limiting middleware
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    
    # Middleware для метрик и логирования
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        """Middleware для измерения времени обработки и сбора метрик."""
        start_time = time.time()
        ACTIVE_CONNECTIONS.inc()
        
        try:
            response = await call_next(request)
            # Security headers (OWASP ASVS):
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Referrer-Policy"] = "no-referrer"
            response.headers["Permissions-Policy"] = (
                "geolocation=(), camera=(), microphone=(), payment=()"
            )
            # CSP: по-умолчанию self; без unsafe-inline. Настраивается далее при необходимости.
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'"
            )
            # HSTS только под HTTPS окружениями
            if request.url.scheme == "https":
                response.headers["Strict-Transport-Security"] = (
                    "max-age=31536000; includeSubDomains; preload"
                )
            
            # Метрики
            process_time = time.time() - start_time
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(process_time)
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code
            ).inc()
            
            # Заголовки
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = getattr(request.state, 'request_id', 'unknown')
            
            return response
            
        except Exception as e:
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=500
            ).inc()
            logger.error(f"Ошибка обработки запроса {request.url.path}: {e}")
            raise
        finally:
            ACTIVE_CONNECTIONS.dec()
    
    # Metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    
    # Health check routes (no prefix for Docker health checks)
    app.include_router(health_router)

    # Экспорт OpenAPI схемы независимо от DEBUG флага для контракт-тестов
    if settings.API_V1_STR and app.openapi_url is None:
        app.openapi_url = "/openapi.json"
    
    # API routes
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Корневой эндпоинт."""
        return {
            "message": "Сервис учета инвестиций",
            "version": settings.APP_VERSION,
            "docs": "/docs" if settings.DEBUG else None,
            "health": "/health",
            "metrics": "/metrics"
        }
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Глобальный обработчик исключений."""
        logger.error(f"Необработанная ошибка: {exc}", exc_info=True)
        
        if settings.DEBUG:
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "error": str(exc),
                    "type": type(exc).__name__
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
    
    return app


# Создание приложения
app = create_application()

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_config=None,  # Используем наш собственный логгер
    )
