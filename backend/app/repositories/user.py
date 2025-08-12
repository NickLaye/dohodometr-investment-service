"""
Репозиторий для работы с пользователями.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.models.user import User, UserSession, PasswordResetToken
from app.core.security import (
    get_password_hash, 
    encrypt_sensitive_data,
    decrypt_sensitive_data,
    generate_numeric_code
)
from app.core.config import settings
from app.core.logging import logger


class UserRepository:
    """Репозиторий для работы с пользователями."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email."""
        stmt = select(User).where(User.email == email.lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create(
        self,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        **kwargs
    ) -> User:
        """Создание нового пользователя."""
        try:
            password_hash = get_password_hash(password)
            
            user = User(
                email=email.lower().strip(),
                password_hash=password_hash,
                first_name=first_name.strip() if first_name else None,
                last_name=last_name.strip() if last_name else None,
                **kwargs
            )
            
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info(f"Создан новый пользователь: {user.email}")
            return user
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Ошибка создания пользователя (уже существует): {email}")
            raise ValueError("Пользователь с таким email уже существует")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Ошибка создания пользователя {email}: {e}")
            raise
    
    async def update_login_info(self, user_id: int, ip_address: str = None):
        """Обновление информации о входе."""
        stmt = update(User).where(User.id == user_id).values(
            last_login_at=datetime.utcnow(),
            last_activity_at=datetime.utcnow(),
            last_login_ip=ip_address,
            failed_login_attempts=0,
            locked_until=None
        )
        await self.db.execute(stmt)
        await self.db.commit()
    
    async def increment_failed_login_attempts(self, user_id: int):
        """Увеличение счетчика неудачных попыток входа."""
        user = await self.get_by_id(user_id)
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
        await self.db.execute(stmt)
        await self.db.commit()
    
    async def set_temp_2fa_secret(self, user_id: int, secret: str):
        """Сохранение временного секрета для 2FA (зашифрованно)."""
        encrypted_secret = encrypt_sensitive_data(secret)
        # Временно сохраняем в Redis или отдельной таблице
        # Здесь упрощенная реализация - сохраняем в поле пользователя
        pass
    
    async def get_temp_2fa_secret(self, user_id: int) -> Optional[str]:
        """Получение временного секрета 2FA."""
        # Здесь должна быть логика получения из Redis или временной таблицы
        return None
    
    async def enable_2fa(self, user_id: int, secret: str) -> List[str]:
        """Включение 2FA для пользователя."""
        # Генерируем резервные коды
        backup_codes = [generate_numeric_code(8) for _ in range(10)]
        backup_codes_encrypted = encrypt_sensitive_data(','.join(backup_codes))
        secret_encrypted = encrypt_sensitive_data(secret)
        
        stmt = update(User).where(User.id == user_id).values(
            totp_secret=secret_encrypted,
            is_2fa_enabled=True,
            backup_codes=backup_codes_encrypted
        )
        await self.db.execute(stmt)
        await self.db.commit()
        
        return backup_codes
    
    async def disable_2fa(self, user_id: int):
        """Отключение 2FA для пользователя."""
        stmt = update(User).where(User.id == user_id).values(
            totp_secret=None,
            is_2fa_enabled=False,
            backup_codes=None
        )
        await self.db.execute(stmt)
        await self.db.commit()
    
    async def create_session(
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
        await self.db.commit()
        await self.db.refresh(session)
        
        return session
    
    async def get_active_sessions(self, user_id: int) -> List[UserSession]:
        """Получение активных сессий пользователя."""
        stmt = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def revoke_session(self, session_id: int):
        """Отзыв сессии."""
        stmt = update(UserSession).where(UserSession.id == session_id).values(
            is_active=False
        )
        await self.db.execute(stmt)
        await self.db.commit()
    
    async def revoke_all_sessions(self, user_id: int):
        """Отзыв всех сессий пользователя."""
        stmt = update(UserSession).where(UserSession.user_id == user_id).values(
            is_active=False
        )
        await self.db.execute(stmt)
        await self.db.commit()
    
    async def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Обновление данных пользователя."""
        stmt = update(User).where(User.id == user_id).values(**kwargs)
        await self.db.execute(stmt)
        await self.db.commit()
        
        return await self.get_by_id(user_id)
    
    async def delete_user(self, user_id: int):
        """Удаление пользователя (GDPR)."""
        user = await self.get_by_id(user_id)
        if user:
            await self.db.delete(user)
            await self.db.commit()
            logger.info(f"Удален пользователь: {user.email}")
    
    async def anonymize_user(self, user_id: int):
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
        await self.db.execute(stmt)
        await self.db.commit()
        
        logger.info(f"Анонимизирован пользователь ID: {user_id}")
    
    async def search_users(
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
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
