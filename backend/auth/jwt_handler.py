"""JWT токены для аутентификации"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from backend.config import settings

# Секретный ключ для JWT (в продакшене должен быть в .env)
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * settings.JWT_EXPIRE_DAYS


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создать JWT токен"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Проверить JWT токен"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_username_from_token(token: str) -> Optional[str]:
    """Получить username из токена"""
    payload = verify_token(token)
    if payload:
        return payload.get("sub")  # "sub" (subject) обычно содержит username
    return None

