"""
Конфигурация приложения для сервиса учета инвестиций.
"""

import secrets
from typing import List, Optional, Any, Dict, Union
from pathlib import Path

from pydantic import (
    PostgresDsn,
    RedisDsn,
    validator,
    EmailStr,
    HttpUrl,
    Field
)
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения."""
    
    # Основные настройки
    APP_NAME: str = "Investment Service"
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # Безопасность
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    JWT_SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = "HS512"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Шифрование для чувствительных данных
    ENCRYPTION_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ENCRYPTION_SALT: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Cryptographic salt for data encryption (required)"
    )
    
    # Пароли
    PASSWORD_MIN_LENGTH: int = 8
    ARGON2_MEMORY_COST: int = 65536
    ARGON2_TIME_COST: int = 3
    ARGON2_PARALLELISM: int = 1
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    RATE_LIMIT_PER_DAY: int = 10000
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_ATTEMPT_RESET_TIME: int = 900  # 15 минут
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "https://dohodometr.ru",
        "https://www.dohodometr.ru",
        "https://api.dohodometr.ru"
    ]
    TRUSTED_HOSTS: List[str] = [
        "localhost", 
        "127.0.0.1", 
        "dohodometr.ru",
        "www.dohodometr.ru",
        "api.dohodometr.ru"
    ]
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # База данных
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "investment_db"
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str = Field(
        default="postgres_dev_only",  
        description="Database password (MUST be changed in production)",
        min_length=12
    )
    DATABASE_ECHO: bool = False
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=values.get("DATABASE_USER"),
            password=values.get("DATABASE_PASSWORD"),
            host=values.get("DATABASE_HOST"),
            port=str(values.get("DATABASE_PORT")),
            path=f"/{values.get('DATABASE_NAME') or ''}",
        )
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[RedisDsn] = None
    
    @validator("REDIS_URL", pre=True)
    def assemble_redis_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return RedisDsn.build(
            scheme="redis",
            password=values.get("REDIS_PASSWORD"),
            host=values.get("REDIS_HOST"),
            port=values.get("REDIS_PORT", 6379),
            path=f"/{values.get('REDIS_DB') or 0}",
        )
    
    # Celery
    CELERY_BROKER_URL: Optional[RedisDsn] = None
    CELERY_RESULT_BACKEND: Optional[RedisDsn] = None
    
    @validator("CELERY_BROKER_URL", pre=True)
    def assemble_celery_broker(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return RedisDsn.build(
            scheme="redis",
            password=values.get("REDIS_PASSWORD"),
            host=values.get("REDIS_HOST"),
            port=values.get("REDIS_PORT", 6379),
            path="/1",
        )
    
    @validator("CELERY_RESULT_BACKEND", pre=True)
    def assemble_celery_result(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return RedisDsn.build(
            scheme="redis",
            password=values.get("REDIS_PASSWORD"),
            host=values.get("REDIS_HOST"),
            port=values.get("REDIS_PORT", 6379),
            path="/2",
        )
    
    # MinIO / S3
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = Field(
        default="minio_dev_access_key",
        description="MinIO access key (MUST be changed in production)",
        min_length=8
    )
    MINIO_SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    MINIO_BUCKET_NAME: str = "investment-files"
    MINIO_SECURE: bool = False
    
    # Email / SMTP
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    EMAIL_FROM: Optional[EmailStr] = None
    
    # Мониторинг
    SENTRY_DSN: Optional[HttpUrl] = None
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PUSHGATEWAY: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    
    # API провайдеры
    MOEX_API_URL: str = "https://iss.moex.com"
    YAHOO_FINANCE_API_URL: str = "https://query1.finance.yahoo.com"
    CBR_API_URL: str = "https://www.cbr-xml-daily.ru"
    
    # Резервное копирование
    BACKUP_ENABLED: bool = True
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_S3_BUCKET: Optional[str] = None
    
    # Feature flags
    FEATURE_BROKER_INTEGRATIONS: bool = False
    FEATURE_TELEGRAM_NOTIFICATIONS: bool = False
    FEATURE_ADVANCED_ANALYTICS: bool = True
    
    # Локализация
    DEFAULT_LOCALE: str = "ru"
    DEFAULT_TIMEZONE: str = "Europe/Moscow"
    DEFAULT_CURRENCY: str = "RUB"
    
    # Загрузка файлов
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: List[str] = ["csv", "xlsx", "xls", "pdf"]
    VIRUS_SCAN_ENABLED: bool = False
    
    # Соответствие российскому законодательству
    DATA_RETENTION_DAYS: int = 2555  # 7 лет (требования валютного законодательства)
    ANONYMIZATION_ENABLED: bool = True
    AUDIT_LOG_RETENTION_DAYS: int = 2555
    
    # 152-ФЗ "О персональных данных"
    STORE_DATA_IN_RF: bool = True
    PDPN_OPERATOR_NOTIFIED: bool = False  # Уведомление Роскомнадзора
    CONSENT_STORAGE_DAYS: int = 2555  # Хранение согласий на обработку ПДн
    
    # 115-ФЗ "Противодействие отмыванию денег"
    AML_MONITORING_ENABLED: bool = True
    SUSPICIOUS_ACTIVITY_THRESHOLD: int = 600000  # 600 тыс руб
    KYC_VERIFICATION_REQUIRED: bool = False  # Для информационного сервиса
    
    # 173-ФЗ "Валютное законодательство"
    CURRENCY_LAW_NOTIFICATIONS: bool = True
    FOREIGN_ACCOUNT_MONITORING: bool = True
    
    # Налоговое законодательство РФ
    TAX_RESIDENT_DEFAULT: bool = True
    NDFL_RATE: float = 0.13  # 13% для резидентов
    IIS_SUPPORT_ENABLED: bool = True
    LDV_CALCULATION_ENABLED: bool = True  # Льгота долгосрочного владения
    
    # Разработка
    MOCK_EXTERNAL_APIS: bool = False
    SEED_DATABASE: bool = False
    
    # Вычисляемые свойства
    @property
    def max_file_size_bytes(self) -> int:
        """Максимальный размер файла в байтах."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024
    
    @property
    def database_url_sync(self) -> str:
        """Синхронный URL для базы данных (для Alembic)."""
        if self.DATABASE_URL:
            return str(self.DATABASE_URL).replace("+asyncpg", "")
        return f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_prefix = ""


# Создание глобального экземпляра настроек
settings = Settings()

# Константы для использования в приложении
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS

# Валидация критически важных настроек
if settings.ENVIRONMENT == "production":
    assert settings.SECRET_KEY != "changeme", "Установите надежный SECRET_KEY для production"
    assert settings.JWT_SECRET_KEY != "changeme", "Установите надежный JWT_SECRET_KEY для production"
    assert settings.DATABASE_PASSWORD not in ["password", "postgres_dev_only"], "Установите надежный пароль базы данных для production"
    assert settings.MINIO_ACCESS_KEY not in ["admin", "minio_dev_only", "minio_dev_access_key"], "Установите надежный MINIO_ACCESS_KEY для production"
    assert len(settings.ENCRYPTION_SALT) >= 32, "ENCRYPTION_SALT должен быть не менее 32 символов для production"
    assert not settings.DEBUG, "Отключите DEBUG режим для production"
