"""
Pydantic схемы для аутентификации.
"""

from typing import Optional, List
from pydantic import BaseModel, EmailStr, validator
from app.core.config import settings


class UserLogin(BaseModel):
    """Схема для входа пользователя."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None  # Допустим email может приходить под именем username (совместимость тестов)
    password: str
    totp_code: Optional[str] = None


class UserRegister(BaseModel):
    """Схема для регистрации пользователя."""
    email: EmailStr
    password: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < settings.PASSWORD_MIN_LENGTH:
            raise ValueError(f'Пароль должен содержать минимум {settings.PASSWORD_MIN_LENGTH} символов')
        return v


class Token(BaseModel):
    """Схема для токенов."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class User(BaseModel):
    """Схема пользователя для ответов API."""
    id: int
    email: EmailStr
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool
    is_verified: bool
    is_2fa_enabled: bool
    locale: str
    timezone: str
    base_currency: str
    
    class Config:
        from_attributes = True


class TwoFactorSetup(BaseModel):
    """Схема для настройки 2FA."""
    secret: str
    qr_code: str
    backup_codes: List[str]


class TwoFactorVerify(BaseModel):
    """Схема для подтверждения 2FA."""
    code: str
