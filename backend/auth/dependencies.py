"""Зависимости для аутентификации"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from backend.auth.jwt_handler import verify_token, get_username_from_token

# HTTPBearer по умолчанию возвращает 403, если заголовок отсутствует
# Используем auto_error=False и обрабатываем вручную для более понятных ошибок
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """Получить текущего пользователя из JWT токена"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Проверяем, что токен передан
    if not credentials:
        logger.warning("Попытка доступа без токена аутентификации (credentials=None)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        token = credentials.credentials
        username = get_username_from_token(token)
        
        if not username:
            logger.warning("Недействительный токен при попытке доступа")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недействительный токен",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return username
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при проверке токена: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ошибка аутентификации",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[str]:
    """Получить текущего пользователя (опционально, для публичных endpoints)"""
    if not credentials:
        return None
    
    token = credentials.credentials
    username = get_username_from_token(token)
    return username

