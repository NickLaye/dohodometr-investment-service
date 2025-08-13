"""
Тесты конфигурации приложения.
"""

import pytest
import os
from unittest.mock import patch
from pydantic import ValidationError

from app.core.config import Settings, validate_production_config


class TestSettings:
    """Тесты класса Settings."""

    def test_default_settings(self):
        """Тест дефолтных настроек."""
        settings = Settings()
        
        assert settings.APP_NAME == "Investment Service"
        assert settings.APP_VERSION == "1.0.0"
        assert settings.API_V1_STR == "/api/v1"
        assert settings.DEBUG is False
        assert settings.ENVIRONMENT == "development"

    def test_settings_from_env(self):
        """Тест загрузки настроек из переменных окружения."""
        with patch.dict(os.environ, {
            'APP_NAME': 'Test App',
            'DEBUG': 'true',
            'ENVIRONMENT': 'testing'
        }):
            settings = Settings()
            
            assert settings.APP_NAME == "Test App"
            assert settings.DEBUG is True
            assert settings.ENVIRONMENT == "testing"

    def test_secret_key_generation(self):
        """Тест автогенерации SECRET_KEY."""
        settings1 = Settings()
        settings2 = Settings()
        
        # Секретные ключи должны быть сгенерированы
        assert len(settings1.SECRET_KEY) >= 32
        assert len(settings1.JWT_SECRET_KEY) >= 32
        
        # И должны быть разными для разных экземпляров
        assert settings1.SECRET_KEY != settings2.SECRET_KEY
        assert settings1.JWT_SECRET_KEY != settings2.JWT_SECRET_KEY

    def test_database_url_validation(self):
        """Тест валидации DATABASE_URL."""
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://user:pass@localhost:5432/test_db'
        }):
            settings = Settings()
            assert str(settings.DATABASE_URL).startswith('postgresql://')

    def test_invalid_database_url(self):
        """Тест невалидного DATABASE_URL."""
        with patch.dict(os.environ, {
            'DATABASE_URL': 'invalid_url'
        }):
            with pytest.raises(ValidationError):
                Settings()

    def test_redis_url_validation(self):
        """Тест валидации REDIS_URL."""
        with patch.dict(os.environ, {
            'REDIS_URL': 'redis://localhost:6379/0'
        }):
            settings = Settings()
            assert str(settings.REDIS_URL).startswith('redis://')

    def test_cors_origins_parsing(self):
        """Тест парсинга CORS_ORIGINS."""
        with patch.dict(os.environ, {
            'CORS_ORIGINS': 'http://localhost:3000,https://example.com'
        }):
            settings = Settings()
            assert len(settings.CORS_ORIGINS) == 2
            assert 'http://localhost:3000' in settings.CORS_ORIGINS
            assert 'https://example.com' in settings.CORS_ORIGINS

    def test_trusted_hosts_parsing(self):
        """Тест парсинга TRUSTED_HOSTS."""
        with patch.dict(os.environ, {
            'TRUSTED_HOSTS': 'localhost,127.0.0.1,example.com'
        }):
            settings = Settings()
            assert len(settings.TRUSTED_HOSTS) == 3
            assert 'localhost' in settings.TRUSTED_HOSTS

    def test_database_url_sync_property(self):
        """Тест свойства database_url_sync."""
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql+asyncpg://user:pass@localhost:5432/test_db'
        }):
            settings = Settings()
            sync_url = settings.database_url_sync
            
            assert 'asyncpg' not in sync_url
            assert sync_url.startswith('postgresql://')

    def test_email_configuration(self):
        """Тест конфигурации email."""
        with patch.dict(os.environ, {
            'SMTP_SERVER': 'smtp.gmail.com',
            'SMTP_PORT': '587',
            'SMTP_USERNAME': 'test@example.com',
            'SMTP_PASSWORD': 'password123',
            'SMTP_USE_TLS': 'true'
        }):
            settings = Settings()
            
            assert settings.SMTP_SERVER == 'smtp.gmail.com'
            assert settings.SMTP_PORT == 587
            assert settings.SMTP_USE_TLS is True

    def test_security_settings(self):
        """Тест настроек безопасности."""
        settings = Settings()
        
        assert settings.JWT_ALGORITHM == "HS512"
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 15
        assert settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS == 7
        assert settings.PASSWORD_MIN_LENGTH == 8
        assert settings.MAX_LOGIN_ATTEMPTS == 5

    def test_rate_limiting_settings(self):
        """Тест настроек rate limiting."""
        settings = Settings()
        
        assert settings.RATE_LIMIT_PER_MINUTE == 60
        assert settings.RATE_LIMIT_PER_HOUR == 1000
        assert settings.RATE_LIMIT_PER_DAY == 10000

    def test_minio_configuration(self):
        """Тест конфигурации MinIO."""
        with patch.dict(os.environ, {
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'admin',
            'MINIO_SECURE': 'false'
        }):
            settings = Settings()
            
            assert settings.MINIO_ENDPOINT == 'localhost:9000'
            assert settings.MINIO_ACCESS_KEY == 'admin'
            assert settings.MINIO_SECURE is False


class TestProductionValidation:
    """Тесты валидации production конфигурации."""

    def test_validate_production_config_success(self):
        """Тест успешной валидации production конфигурации."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'SECRET_KEY': 'very_secure_secret_key_for_production_use_123',
            'JWT_SECRET_KEY': 'very_secure_jwt_secret_key_for_production_use_123',
            'DATABASE_URL': 'postgresql://user:pass@db:5432/prod_db',
            'REDIS_URL': 'redis://redis:6379/0'
        }):
            settings = Settings()
            # Не должно быть исключений
            validate_production_config(settings)

    def test_validate_production_config_weak_secrets(self):
        """Тест валидации с слабыми секретами."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'SECRET_KEY': 'changeme',
            'JWT_SECRET_KEY': 'changeme'
        }):
            settings = Settings()
            
            with pytest.raises(AssertionError, match="SECRET_KEY"):
                validate_production_config(settings)

    def test_validate_production_config_debug_enabled(self):
        """Тест валидации с включенным DEBUG в production."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'DEBUG': 'true',
            'SECRET_KEY': 'very_secure_secret_key_for_production_use_123',
            'JWT_SECRET_KEY': 'very_secure_jwt_secret_key_for_production_use_123'
        }):
            settings = Settings()
            
            with pytest.raises(AssertionError, match="DEBUG"):
                validate_production_config(settings)

    def test_development_environment_allows_weak_secrets(self):
        """Тест что в development окружении слабые секреты допустимы."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'development',
            'SECRET_KEY': 'changeme',
            'JWT_SECRET_KEY': 'changeme',
            'DEBUG': 'true'
        }):
            settings = Settings()
            # Не должно быть исключений в development
            # validate_production_config вызывается только для production


class TestConfigUtils:
    """Тесты утилит конфигурации."""

    def test_settings_model_validation(self):
        """Тест валидации модели настроек."""
        # Тест с невалидными типами данных
        with patch.dict(os.environ, {
            'RATE_LIMIT_PER_MINUTE': 'not_a_number'
        }):
            with pytest.raises(ValidationError):
                Settings()

    def test_bool_environment_variables(self):
        """Тест булевых переменных окружения."""
        test_cases = [
            ('true', True),
            ('false', False),
            ('1', True),
            ('0', False),
            ('yes', True),
            ('no', False),
            ('on', True),
            ('off', False)
        ]
        
        for env_value, expected in test_cases:
            with patch.dict(os.environ, {'DEBUG': env_value}):
                settings = Settings()
                assert settings.DEBUG == expected

    def test_list_environment_variables(self):
        """Тест списковых переменных окружения."""
        with patch.dict(os.environ, {
            'CORS_ORIGINS': 'http://localhost:3000, https://example.com,  https://test.com  '
        }):
            settings = Settings()
            
            # Должны быть очищены от пробелов
            assert len(settings.CORS_ORIGINS) == 3
            assert 'http://localhost:3000' in settings.CORS_ORIGINS
            assert 'https://example.com' in settings.CORS_ORIGINS
            assert 'https://test.com' in settings.CORS_ORIGINS

    def test_password_strength_requirements(self):
        """Тест требований к силе паролей."""
        settings = Settings()
        
        # Проверяем что минимальная длина пароля разумная
        assert settings.PASSWORD_MIN_LENGTH >= 8
        
        # Проверяем настройки Argon2
        assert settings.ARGON2_MEMORY_COST >= 65536
        assert settings.ARGON2_TIME_COST >= 3
        assert settings.ARGON2_PARALLELISM >= 1
