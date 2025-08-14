"""
Репозиторий для работы с пользователями.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.models.user import User, UserSession, PasswordResetToken
from app.core.security import (
    hash_password,
    verify_password,
    encrypt_sensitive_data,
    decrypt_sensitive_data,
    generate_numeric_code
)
from app.core.config import settings
from app.core.logging import logger
from app.schemas.auth import UserCreate


class UserRepository:
    """Репозиторий для работы с пользователями."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID."""
        stmt = select(User).where(User.id == user_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email."""
        stmt = select(User).where(User.email == email.lower())
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    def create(self, data: UserCreate) -> User:
        """Создание нового пользователя из схемы."""
        try:
            password_hash = hash_password(data.password)
            
            user = User(
                email=data.email.lower().strip(),
                username=data.username,
                full_name=data.full_name,
                hashed_password=password_hash,
                is_active=True,
                is_superuser=False,
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Создан новый пользователь: {user.email}")
            return user
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Ошибка создания пользователя (уже существует): {data.email}")
            raise ValueError("Пользователь с таким email уже существует")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка создания пользователя {data.email}: {e}")
            raise
    
    def authenticate(self, email: str, password: str) -> Optional[User]:
        """Аутентификация пользователя по email и паролю."""
        user = self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    def update_login_info(self, user_id: int, ip_address: str = None):
        """Обновление информации о входе."""
        stmt = update(User).where(User.id == user_id).values(
            last_login_at=datetime.utcnow(),
            last_activity_at=datetime.utcnow(),
            last_login_ip=ip_address,
            failed_login_attempts=0,
            locked_until=None
        )
        self.db.execute(stmt)
        self.db.commit()
    
    def increment_failed_login_attempts(self, user_id: int):
        """Увеличение счетчика неудачных попыток входа."""
        user = self.get_by_id(user_id)
        if not user:
            return
        
        failed_attempts = user.failed_login_attempts + 1
        locked_until = None
        
        # Блокируем аккаунт после превышения лимита попыток
        if failed_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            locked_until = datetime.utcnow() + timedelta(seconds=settings.LOGIN_ATTEMPT_RESET_TIME)
        
        stmt = update(User).where(User.id == user_id).values(
            failed_login_attempts=failed_attempts,
            locked_until=locked_until
        )
        self.db.execute(stmt)
        self.db.commit()
    
    def set_temp_2fa_secret(self, user_id: int, secret: str):
        """Сохранение временного секрета для 2FA (зашифрованно)."""
        encrypted_secret = encrypt_sensitive_data(secret)
        # TODO: реализовать хранение в Redis
        return None
    
    def get_temp_2fa_secret(self, user_id: int) -> Optional[str]:
        """Получение временного секрета 2FA."""
        # TODO: реализовать получение из Redis
        return None
    
    def enable_2fa(self, user_id: int, secret: str) -> List[str]:
        """Включение 2FA для пользователя."""
        backup_codes = [generate_numeric_code(8) for _ in range(10)]
        backup_codes_encrypted = encrypt_sensitive_data(','.join(backup_codes))
        secret_encrypted = encrypt_sensitive_data(secret)
        
        stmt = update(User).where(User.id == user_id).values(
            totp_secret=secret_encrypted,
            is_2fa_enabled=True,
            backup_codes=backup_codes_encrypted
        )
        self.db.execute(stmt)
        self.db.commit()
        
        return backup_codes
    
    def disable_2fa(self, user_id: int):
        """Отключение 2FA для пользователя."""
        stmt = update(User).where(User.id == user_id).values(
            totp_secret=None,
            is_2fa_enabled=False,
            backup_codes=None
        )
        self.db.execute(stmt)
        self.db.commit()
    
    def create_session(
        self,
        user_id: int,
        refresh_token_jti: str,
        expires_at: datetime,
        user_agent: str = None,
        ip_address: str = None
    ) -> UserSession:
        """Создание пользовательской сессии."""
        session = UserSession(
            user_id=user_id,
            refresh_token_jti=refresh_token_jti,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        return session
    
    def get_active_sessions(self, user_id: int) -> List[UserSession]:
        """Получение активных сессий пользователя."""
        stmt = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        )
        result = self.db.execute(stmt)
        return result.scalars().all()
    
    def revoke_session(self, session_id: int):
        """Отзыв сессии."""
        stmt = update(UserSession).where(UserSession.id == session_id).values(
            is_active=False
        )
        self.db.execute(stmt)
        self.db.commit()
    
    def revoke_all_sessions(self, user_id: int):
        """Отзыв всех сессий пользователя."""
        stmt = update(UserSession).where(UserSession.user_id == user_id).values(
            is_active=False
        )
        self.db.execute(stmt)
        self.db.commit()
    
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Обновление данных пользователя."""
        stmt = update(User).where(User.id == user_id).values(**kwargs)
        self.db.execute(stmt)
        self.db.commit()
        
        return self.get_by_id(user_id)
    
    def delete_user(self, user_id: int):
        """Удаление пользователя (GDPR)."""
        user = self.get_by_id(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()
            logger.info(f"Удален пользователь: {user.email}")
    
    def anonymize_user(self, user_id: int):
        """Анонимизация пользователя (GDPR)."""
        anonymous_email = f"deleted_{user_id}@deleted.local"
        
        stmt = update(User).where(User.id == user_id).values(
            email=anonymous_email,
            first_name=None,
            last_name=None,
            totp_secret=None,
            backup_codes=None,
            is_active=False,
            is_verified=False,
            is_2fa_enabled=False
        )
        self.db.execute(stmt)
        self.db.commit()
        
        logger.info(f"Анонимизирован пользователь ID: {user_id}")
    
    def search_users(
        self,
        query: str = None,
        is_active: bool = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[User]:
        """Поиск пользователей (для админки)."""
        stmt = select(User)
        
        if query:
            stmt = stmt.where(
                User.email.ilike(f"%{query}%") |
                User.first_name.ilike(f"%{query}%") |
                User.last_name.ilike(f"%{query}%")
            )
        
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        
        stmt = stmt.offset(offset).limit(limit)
        
        result = self.db.execute(stmt)
        return result.scalars().all()
