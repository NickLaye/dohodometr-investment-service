"""
Эндпоинты аутентификации для сервиса учета инвестиций.
"""

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database_sync import get_db
from app.core.security import (
    create_access_token, 
    create_refresh_token,
    verify_password,
    get_password_hash,
    verify_token,
    generate_totp_secret,
    generate_totp_qr_code,
    verify_totp_token,
    get_current_user
)
from app.core.logging import logger, log_security_event
from app.schemas.auth import (
    Token, 
    UserLogin, 
    UserRegister, 
    User as UserSchema,
    TwoFactorSetup,
    TwoFactorVerify
)
from app.models.user import User
from app.repositories.user import UserRepository

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
) -> Any:
    """
    Регистрация нового пользователя.
    """
    user_repo = UserRepository(db)
    
    # Проверяем, существует ли пользователь с таким email
    existing_user = user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )
    
    # Создаем нового пользователя
    try:
        user = user_repo.create(
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name
        )
        
        log_security_event(
            "user_registered",
            user_id=user.id,
            details={"email": user_data.email}
        )
        
        return user
        
    except Exception as e:
        logger.error(f"Ошибка регистрации пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка создания пользователя"
        )


@router.post("/login", response_model=Token)
def login(
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
) -> Any:
    """
    Аутентификация пользователя и получение токенов.
    """
    user_repo = UserRepository(db)
    
    # Получаем пользователя по email
    user = user_repo.get_by_email(user_credentials.email)
    if not user:
        log_security_event(
            "login_failed",
            details={"email": user_credentials.email, "reason": "user_not_found"},
            success=False
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные"
        )
    
    # Проверяем пароль
    if not verify_password(user_credentials.password, user.password_hash):
        user_repo.increment_failed_login_attempts(user.id)
        log_security_event(
            "login_failed",
            user_id=user.id,
            details={"reason": "invalid_password"},
            success=False
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные"
        )
    
    # Проверяем, может ли пользователь войти
    if not user.can_login():
        log_security_event(
            "login_blocked",
            user_id=user.id,
            details={"reason": "account_locked_or_inactive"},
            success=False
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт заблокирован или неактивен"
        )
    
    # Проверяем 2FA если включен
    if user.is_2fa_enabled:
        if not user_credentials.totp_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Требуется код двухфакторной аутентификации"
            )
        
        if not verify_totp_token(user.totp_secret, user_credentials.totp_code):
            log_security_event(
                "2fa_failed",
                user_id=user.id,
                success=False
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный код двухфакторной аутентификации"
            )
    
    # Создаем токены
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    # Обновляем информацию о входе
    user_repo.update_login_info(user.id)
    
    log_security_event(
        "login_successful",
        user_id=user.id,
        details={"2fa_used": user.is_2fa_enabled}
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_token: str = Body(..., embed=True),
    db: Session = Depends(get_db)
) -> Any:
    """
    Обновление access токена с помощью refresh токена.
    """
    try:
        # Проверяем refresh токен
        payload = verify_token(refresh_token, "refresh")
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недействительный токен"
            )
        
        # Проверяем, существует ли пользователь
        user_repo = UserRepository(db)
        user = user_repo.get_by_id(int(user_id))
        
        if not user or not user.can_login():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Пользователь не найден или заблокирован"
            )
        
        # Создаем новые токены
        new_access_token = create_access_token(subject=user.id)
        new_refresh_token = create_refresh_token(subject=user.id)
        
        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )
        
    except Exception as e:
        logger.error(f"Ошибка обновления токена: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен"
        )


@router.post("/2fa/setup", response_model=TwoFactorSetup)
def setup_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Настройка двухфакторной аутентификации.
    """
    if current_user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA уже включена"
        )
    
    # Генерируем секрет и QR код
    secret = generate_totp_secret()
    qr_code = generate_totp_qr_code(current_user.email, secret)
    
    # Сохраняем секрет (временно, до подтверждения)
    user_repo = UserRepository(db)
    user_repo.set_temp_2fa_secret(current_user.id, secret)
    
    return TwoFactorSetup(
        secret=secret,
        qr_code=qr_code,
        backup_codes=[]  # Генерируем после подтверждения
    )


@router.post("/2fa/verify")
def verify_2fa(
    verification: TwoFactorVerify,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Подтверждение настройки двухфакторной аутентификации.
    """
    user_repo = UserRepository(db)
    
    # Получаем временный секрет
    temp_secret = user_repo.get_temp_2fa_secret(current_user.id)
    if not temp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Секрет 2FA не найден. Повторите настройку"
        )
    
    # Проверяем код
    if not verify_totp_token(temp_secret, verification.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный код подтверждения"
        )
    
    # Активируем 2FA
    backup_codes = user_repo.enable_2fa(current_user.id, temp_secret)
    
    log_security_event(
        "2fa_enabled",
        user_id=current_user.id
    )
    
    return {"message": "2FA успешно настроена", "backup_codes": backup_codes}


@router.post("/2fa/disable")
def disable_2fa(
    verification: TwoFactorVerify,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Отключение двухфакторной аутентификации.
    """
    if not current_user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA не включена"
        )
    
    # Проверяем код
    if not verify_totp_token(current_user.totp_secret, verification.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный код подтверждения"
        )
    
    # Отключаем 2FA
    user_repo = UserRepository(db)
    user_repo.disable_2fa(current_user.id)
    
    log_security_event(
        "2fa_disabled",
        user_id=current_user.id
    )
    
    return {"message": "2FA успешно отключена"}


@router.get("/me", response_model=UserSchema)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Получение информации о текущем пользователе.
    """
    return current_user


@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Выход из системы (добавление токена в черный список).
    """
    # TODO: Добавить токен в blacklist через Redis
    
    log_security_event(
        "logout",
        user_id=current_user.id
    )
    
    return {"message": "Выход выполнен успешно"}
