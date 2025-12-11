"""API endpoints для аутентификации"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional
from datetime import timedelta

from backend.models.user import User
from backend.auth.jwt_handler import create_access_token
from backend.auth.dependencies import get_current_user

router = APIRouter()


class RegisterRequest(BaseModel):
    """Запрос на регистрацию"""
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    password: str = Field(..., min_length=6, max_length=100, description="Пароль")
    secret_code: str = Field(..., min_length=4, max_length=50, description="Секретный код для восстановления пароля")


class LoginRequest(BaseModel):
    """Запрос на вход"""
    username: str = Field(..., description="Имя пользователя")
    password: str = Field(..., description="Пароль")


class RecoverPasswordRequest(BaseModel):
    """Запрос на восстановление пароля"""
    username: str = Field(..., description="Имя пользователя")
    secret_code: str = Field(..., description="Секретный код")
    new_password: str = Field(..., min_length=6, max_length=100, description="Новый пароль")


class ChangePasswordRequest(BaseModel):
    """Запрос на изменение пароля"""
    old_password: str = Field(..., description="Старый пароль")
    new_password: str = Field(..., min_length=6, max_length=100, description="Новый пароль")


class TokenResponse(BaseModel):
    """Ответ с токеном"""
    access_token: str
    token_type: str = "bearer"
    username: str


class UserResponse(BaseModel):
    """Ответ с данными пользователя"""
    username: str
    created_at: Optional[str] = None
    last_login: Optional[str] = None


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """Регистрация нового пользователя"""
    # Проверка, существует ли пользователь
    if User.exists(request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже существует"
        )
    
    # Создание пользователя
    try:
        user = User.create(
            username=request.username,
            password=request.password,
            secret_code=request.secret_code
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Создание токена
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(days=7)
    )
    
    return TokenResponse(
        access_token=access_token,
        username=user.username
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Вход в систему"""
    # Загрузка пользователя
    user = User(request.username)
    if not user.load():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль"
        )
    
    # Проверка пароля
    if not user.verify_password(request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль"
        )
    
    # Обновление времени последнего входа
    user.update_last_login()
    
    # Создание токена
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(days=7)
    )
    
    return TokenResponse(
        access_token=access_token,
        username=user.username
    )


@router.post("/recover-password", status_code=status.HTTP_200_OK)
async def recover_password(request: RecoverPasswordRequest):
    """Восстановление пароля по секретному коду"""
    # Загрузка пользователя
    user = User(request.username)
    if not user.load():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Проверка секретного кода
    if not user.verify_secret_code(request.secret_code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный секретный код"
        )
    
    # Установка нового пароля
    user.set_password(request.new_password)
    user.save()
    
    return {"message": "Пароль успешно изменён"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(username: str = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    user = User(username)
    if not user.load():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    return UserResponse(
        username=user.username,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login=user.last_login.isoformat() if user.last_login else None,
    )


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    request: ChangePasswordRequest,
    username: str = Depends(get_current_user)
):
    """Изменить пароль (требует аутентификации)"""
    user = User(username)
    if not user.load():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Проверка старого пароля
    if not user.verify_password(request.old_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный старый пароль"
        )
    
    # Установка нового пароля
    user.set_password(request.new_password)
    user.save()
    
    return {"message": "Пароль успешно изменён"}

