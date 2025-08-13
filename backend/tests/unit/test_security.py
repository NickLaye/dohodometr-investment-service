"""
Тесты модуля безопасности.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    verify_password,
    get_password_hash,
    generate_totp_secret,
    verify_totp_code,
    encrypt_sensitive_data,
    decrypt_sensitive_data
)
from app.core.config import settings


class TestPasswordHashing:
    """Тесты хеширования паролей."""

    def test_password_hashing(self):
        """Тест хеширования и верификации пароля."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False

    def test_different_hashes_for_same_password(self):
        """Тест что одинаковые пароли дают разные хеши (из-за соли)."""
        password = "test_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Тесты JWT токенов."""

    def test_create_access_token(self):
        """Тест создания access токена."""
        user_id = 123
        token = create_access_token(user_id)
        
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Тест создания refresh токена."""
        user_id = 123
        token = create_refresh_token(user_id)
        
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_valid_token(self):
        """Тест верификации валидного токена."""
        user_id = 123
        token = create_access_token(user_id)
        payload = verify_token(token)
        
        assert payload is not None
        assert payload.get("sub") == str(user_id)
        assert payload.get("type") == "access"

    def test_verify_invalid_token(self):
        """Тест верификации невалидного токена."""
        invalid_token = "invalid.token.here"
        payload = verify_token(invalid_token)
        
        assert payload is None

    def test_token_expiration(self):
        """Тест что токен становится невалидным после истечения срока."""
        user_id = 123
        
        # Создаем токен с коротким сроком жизни
        with patch.object(settings, 'JWT_ACCESS_TOKEN_EXPIRE_MINUTES', -1):
            token = create_access_token(user_id)
        
        # Токен должен быть просроченным
        payload = verify_token(token)
        assert payload is None

    def test_token_types(self):
        """Тест различных типов токенов."""
        user_id = 123
        
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        
        access_payload = verify_token(access_token)
        refresh_payload = verify_token(refresh_token)
        
        assert access_payload.get("type") == "access"
        assert refresh_payload.get("type") == "refresh"


class TestTOTP:
    """Тесты TOTP (Two-Factor Authentication)."""

    def test_generate_totp_secret(self):
        """Тест генерации TOTP секрета."""
        secret = generate_totp_secret()
        
        assert isinstance(secret, str)
        assert len(secret) == 32  # Base32 encoded secret

    def test_verify_totp_code_with_valid_secret(self):
        """Тест верификации TOTP кода с валидным секретом."""
        secret = generate_totp_secret()
        
        # Генерируем код для текущего времени
        import pyotp
        totp = pyotp.TOTP(secret)
        current_code = totp.now()
        
        # Проверяем код
        is_valid = verify_totp_code(secret, current_code)
        assert is_valid is True

    def test_verify_totp_code_with_invalid_code(self):
        """Тест верификации TOTP с невалидным кодом."""
        secret = generate_totp_secret()
        invalid_code = "000000"
        
        is_valid = verify_totp_code(secret, invalid_code)
        assert is_valid is False

    def test_verify_totp_code_with_invalid_secret(self):
        """Тест верификации TOTP с невалидным секретом."""
        invalid_secret = "INVALID_SECRET"
        code = "123456"
        
        is_valid = verify_totp_code(invalid_secret, code)
        assert is_valid is False


class TestDataEncryption:
    """Тесты шифрования чувствительных данных."""

    def test_encrypt_decrypt_sensitive_data(self):
        """Тест шифрования и расшифровки данных."""
        original_data = "sensitive_information_123"
        
        encrypted = encrypt_sensitive_data(original_data)
        decrypted = decrypt_sensitive_data(encrypted)
        
        assert encrypted != original_data
        assert decrypted == original_data

    def test_encrypt_same_data_gives_different_results(self):
        """Тест что одинаковые данные дают разные зашифрованные результаты."""
        data = "test_data"
        
        encrypted1 = encrypt_sensitive_data(data)
        encrypted2 = encrypt_sensitive_data(data)
        
        # Результаты должны быть разными из-за случайного IV
        assert encrypted1 != encrypted2
        
        # Но оба должны расшифровываться в исходные данные
        assert decrypt_sensitive_data(encrypted1) == data
        assert decrypt_sensitive_data(encrypted2) == data

    def test_decrypt_invalid_data(self):
        """Тест расшифровки невалидных данных."""
        invalid_encrypted = "invalid_encrypted_data"
        
        with pytest.raises(Exception):
            decrypt_sensitive_data(invalid_encrypted)

    def test_encrypt_empty_data(self):
        """Тест шифрования пустых данных."""
        empty_data = ""
        
        encrypted = encrypt_sensitive_data(empty_data)
        decrypted = decrypt_sensitive_data(encrypted)
        
        assert decrypted == empty_data

    def test_encrypt_unicode_data(self):
        """Тест шифрования Unicode данных."""
        unicode_data = "Тест с русскими символами и эмодзи 🔒"
        
        encrypted = encrypt_sensitive_data(unicode_data)
        decrypted = decrypt_sensitive_data(encrypted)
        
        assert decrypted == unicode_data


class TestSecurityHelpers:
    """Тесты вспомогательных функций безопасности."""

    def test_password_strength_validation(self):
        """Тест валидации силы пароля."""
        # Эти тесты нужно будет добавить когда будет реализована функция
        # validate_password_strength в модуле security
        pass

    def test_rate_limiting_helpers(self):
        """Тест вспомогательных функций rate limiting."""
        # Эти тесты нужно будет добавить когда будут реализованы функции
        # rate limiting в модуле security
        pass


@pytest.mark.asyncio
class TestAsyncSecurity:
    """Тесты асинхронных функций безопасности."""

    async def test_async_token_validation(self):
        """Тест асинхронной валидации токенов."""
        # Если будут асинхронные функции валидации токенов
        pass
