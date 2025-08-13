"""
Модель пользователя для сервиса учета инвестиций.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, 
    UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database_sync import Base


class User(Base):
    """Модель пользователя."""
    
    __tablename__ = "users"
    
    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Персональная информация
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Настройки пользователя
    locale: Mapped[str] = mapped_column(String(10), default="ru", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="Europe/Moscow", nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)
    
    # 2FA настройки (зашифрованы)
    totp_secret: Mapped[Optional[str]] = mapped_column(Text)  # Зашифровано
    is_2fa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    backup_codes: Mapped[Optional[str]] = mapped_column(Text)  # Зашифровано, JSON список
    
    # Статус и права
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Безопасность
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime)
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Метаданные
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # IP адреса для аудита
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(45))  # IPv6 поддержка
    registration_ip: Mapped[Optional[str]] = mapped_column(String(45))
    
    # Настройки уведомлений
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    push_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # GDPR поля
    data_processing_consent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    marketing_consent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    consent_given_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Отношения с другими таблицами (пока закомментированы)
    # portfolios: Mapped[List["Portfolio"]] = relationship(
    #     "Portfolio", 
    #     back_populates="owner",
    #     cascade="all, delete-orphan"
    # )
    
    # goals: Mapped[List["Goal"]] = relationship(
    #     "Goal",
    #     back_populates="user",
    #     cascade="all, delete-orphan"
    # )
    
    # alerts: Mapped[List["Alert"]] = relationship(
    #     "Alert",
    #     back_populates="user", 
    #     cascade="all, delete-orphan"
    # )
    
    # notifications: Mapped[List["Notification"]] = relationship(
    #     "Notification",
    #     back_populates="user",
    #     cascade="all, delete-orphan"
    # )
    
    # imports: Mapped[List["Import"]] = relationship(
    #     "Import",
    #     back_populates="user",
    #     cascade="all, delete-orphan"
    # )
    
    # broker_connections: Mapped[List["BrokerConnection"]] = relationship(
    #     "BrokerConnection",
    #     back_populates="user",
    #     cascade="all, delete-orphan"
    # )
    
    # tags: Mapped[List["Tag"]] = relationship(
    #     "Tag",
    #     back_populates="user",
    #     cascade="all, delete-orphan"
    # )
    
    # Ограничения и индексы
    __table_args__ = (
        # Уникальный индекс на email (case-insensitive)
        Index('ix_users_email_lower', func.lower(email), unique=True),
        
        # Составной индекс для поиска активных пользователей
        Index('ix_users_active_verified', 'is_active', 'is_verified'),
        
        # Индекс для поиска заблокированных пользователей
        Index('ix_users_locked', 'locked_until'),
        
        # Проверочные ограничения
        CheckConstraint('failed_login_attempts >= 0', name='ck_users_failed_attempts_positive'),
        CheckConstraint('length(email) >= 5', name='ck_users_email_min_length'),
        CheckConstraint('length(password_hash) >= 10', name='ck_users_password_hash_min_length'),
        CheckConstraint('base_currency ~ \'^[A-Z]{3}$\'', name='ck_users_base_currency_format'),
        CheckConstraint('locale ~ \'^[a-z]{2}(_[A-Z]{2})?$\'', name='ck_users_locale_format'),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', active={self.is_active})>"
    
    @property
    def full_name(self) -> str:
        """Полное имя пользователя."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.email.split('@')[0]
    
    @property
    def is_locked(self) -> bool:
        """Проверка, заблокирован ли пользователь."""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    def can_login(self) -> bool:
        """Может ли пользователь войти в систему."""
        return (
            self.is_active and 
            self.is_verified and 
            not self.is_locked
        )


class UserSession(Base):
    """Модель пользовательской сессии."""
    
    __tablename__ = "user_sessions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Токены
    refresh_token_jti: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    
    # Метаданные сессии
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    device_info: Mapped[Optional[str]] = mapped_column(Text)  # JSON с информацией об устройстве
    
    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Статус
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Индексы
    __table_args__ = (
        Index('ix_user_sessions_user_active', 'user_id', 'is_active'),
        Index('ix_user_sessions_expires', 'expires_at'),
        Index('ix_user_sessions_refresh_token', 'refresh_token_jti'),
    )
    
    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"


class PasswordResetToken(Base):
    """Модель для токенов сброса пароля."""
    
    __tablename__ = "password_reset_tokens"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Токен (хешированный)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    
    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Статус
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Метаданные
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    
    # Индексы
    __table_args__ = (
        Index('ix_password_reset_user_active', 'user_id', 'is_used'),
        Index('ix_password_reset_expires', 'expires_at'),
        Index('ix_password_reset_token', 'token_hash'),
    )
    
    def __repr__(self) -> str:
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id}, used={self.is_used})>"
