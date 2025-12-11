"""Зависимости для аутентификации"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from backend.auth.jwt_handler import verify_token, get_username_from_token

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Получить текущего пользователя из JWT токена"""
    token = credentials.credentials
    username = get_username_from_token(token)
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return username


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[str]:
    """Получить текущего пользователя (опционально, для публичных endpoints)"""
    if not credentials:
        return None
    
    token = credentials.credentials
    username = get_username_from_token(token)
    return username

