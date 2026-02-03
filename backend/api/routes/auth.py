"""API endpoints для аутентификации"""
from fastapi import APIRouter, HTTPException, status, Depends, Body
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import timedelta
from sqlalchemy.orm import Session
import re

from backend.models.user import User
from backend.auth.jwt_handler import create_access_token
from backend.auth.dependencies import get_current_user
from backend.database import get_db

router = APIRouter()


class RegisterRequest(BaseModel):
    """Запрос на регистрацию"""
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    password: str = Field(..., min_length=6, max_length=72, description="Пароль")
    secret_code: str = Field(..., min_length=4, max_length=72, description="Секретный код для восстановления пароля")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Валидация username: только латинские буквы, цифры, подчеркивание и дефис"""
        if not v:
            raise ValueError("Имя пользователя не может быть пустым")
        
        # Убираем пробелы в начале и конце
        v = v.strip()
        
        if not v:
            raise ValueError("Имя пользователя не может состоять только из пробелов")
        
        if len(v) < 3:
            raise ValueError("Имя пользователя должно содержать минимум 3 символа")
        
        if len(v) > 50:
            raise ValueError("Имя пользователя не может быть длиннее 50 символов")
        
        # Строгая проверка: только латинские буквы (a-z, A-Z), цифры (0-9), подчеркивание (_) и дефис (-)
        # Проверяем, что НЕТ кириллицы и других нелатинских символов
        if re.search(r'[^\x00-\x7F]', v):
            # Если есть не-ASCII символы, проверяем конкретно на кириллицу
            if re.search(r'[а-яА-ЯёЁ]', v):
                raise ValueError(
                    "Имя пользователя может содержать только латинские буквы (a-z, A-Z), цифры (0-9), подчеркивание (_) и дефис (-). Кириллица и другие нелатинские символы не допускаются."
                )
            else:
                raise ValueError(
                    "Имя пользователя может содержать только латинские буквы (a-z, A-Z), цифры (0-9), подчеркивание (_) и дефис (-). Другие символы не допускаются."
                )
        
        # Проверка на только латинские буквы, цифры, подчеркивание и дефис
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError(
                "Имя пользователя может содержать только латинские буквы (a-z, A-Z), цифры (0-9), подчеркивание (_) и дефис (-). Другие символы не допускаются."
            )
        
        # Не может начинаться или заканчиваться дефисом или подчеркиванием
        if v.startswith('-') or v.startswith('_') or v.endswith('-') or v.endswith('_'):
            raise ValueError("Имя пользователя не может начинаться или заканчиваться дефисом или подчеркиванием")
        
        # Не может быть только цифрами
        if v.isdigit():
            raise ValueError("Имя пользователя не может состоять только из цифр")
        
        # Должна быть хотя бы одна латинская буква
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError("Имя пользователя должно содержать хотя бы одну латинскую букву")
        
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Валидация пароля"""
        if not v:
            raise ValueError("Пароль не может быть пустым")
        
        # Убираем пробелы в начале и конце
        v = v.strip()
        
        if not v:
            raise ValueError("Пароль не может состоять только из пробелов")
        
        if len(v) < 6:
            raise ValueError("Пароль должен содержать минимум 6 символов")
        
        # Проверка на нелатинские символы (кириллица и другие)
        if re.search(r'[^\x00-\x7F]', v):
            if re.search(r'[а-яА-ЯёЁ]', v):
                raise ValueError("Пароль может содержать только латинские буквы, цифры и специальные символы. Кириллица не допускается.")
            else:
                raise ValueError("Пароль может содержать только латинские буквы, цифры и специальные символы. Другие символы не допускаются.")
        
        # Проверка на допустимые символы: латинские буквы, цифры и специальные символы
        if not re.match(r'^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]+$', v):
            raise ValueError("Пароль может содержать только латинские буквы, цифры и специальные символы")
        
        # Проверка длины в байтах (bcrypt ограничивает до 72 байт)
        v_bytes = v.encode('utf-8')
        if len(v_bytes) > 72:
            raise ValueError("Пароль слишком длинный (максимум 72 байта в UTF-8)")
        
        # Проверка на наличие хотя бы одной буквы и одной цифры
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError("Пароль должен содержать хотя бы одну латинскую букву")
        
        if not re.search(r'[0-9]', v):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        
        return v
    
    @field_validator('secret_code')
    @classmethod
    def validate_secret_code(cls, v: str) -> str:
        """Валидация секретного кода"""
        if not v:
            raise ValueError("Секретный код не может быть пустым")
        
        # Убираем пробелы в начале и конце
        v = v.strip()
        
        if not v:
            raise ValueError("Секретный код не может состоять только из пробелов")
        
        if len(v) < 4:
            raise ValueError("Секретный код должен содержать минимум 4 символа")
        
        # Проверка на нелатинские символы (кириллица и другие)
        if re.search(r'[^\x00-\x7F]', v):
            if re.search(r'[а-яА-ЯёЁ]', v):
                raise ValueError("Секретный код может содержать только латинские буквы, цифры и специальные символы. Кириллица не допускается.")
            else:
                raise ValueError("Секретный код может содержать только латинские буквы, цифры и специальные символы. Другие символы не допускаются.")
        
        # Проверка на допустимые символы: латинские буквы, цифры и специальные символы
        if not re.match(r'^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]+$', v):
            raise ValueError("Секретный код может содержать только латинские буквы, цифры и специальные символы")
        
        # Проверка длины в байтах (bcrypt ограничивает до 72 байт)
        v_bytes = v.encode('utf-8')
        if len(v_bytes) > 72:
            raise ValueError("Секретный код слишком длинный (максимум 72 байта в UTF-8)")
        
        return v


class LoginRequest(BaseModel):
    """Запрос на вход"""
    username: str = Field(..., description="Имя пользователя")
    password: str = Field(..., description="Пароль")


class RecoverPasswordRequest(BaseModel):
    """Запрос на восстановление пароля"""
    username: str = Field(..., description="Имя пользователя")
    secret_code: str = Field(..., description="Секретный код")
    new_password: str = Field(..., min_length=6, max_length=72, description="Новый пароль")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Валидация username"""
        if not v:
            raise ValueError("Имя пользователя не может быть пустым")
        v = v.strip()
        if not v:
            raise ValueError("Имя пользователя не может состоять только из пробелов")
        if len(v) > 50:
            raise ValueError("Имя пользователя не может быть длиннее 50 символов")
        return v
    
    @field_validator('secret_code')
    @classmethod
    def validate_secret_code(cls, v: str) -> str:
        """Валидация секретного кода"""
        if not v:
            raise ValueError("Секретный код не может быть пустым")
        v = v.strip()
        if not v:
            raise ValueError("Секретный код не может состоять только из пробелов")
        
        # Проверка на нелатинские символы
        if re.search(r'[^\x00-\x7F]', v):
            if re.search(r'[а-яА-ЯёЁ]', v):
                raise ValueError("Секретный код может содержать только латинские буквы, цифры и специальные символы. Кириллица не допускается.")
            else:
                raise ValueError("Секретный код может содержать только латинские буквы, цифры и специальные символы. Другие символы не допускаются.")
        
        if not re.match(r'^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]+$', v):
            raise ValueError("Секретный код может содержать только латинские буквы, цифры и специальные символы")
        
        v_bytes = v.encode('utf-8')
        if len(v_bytes) > 72:
            raise ValueError("Секретный код слишком длинный (максимум 72 байта в UTF-8)")
        return v
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Валидация нового пароля"""
        if not v:
            raise ValueError("Пароль не может быть пустым")
        v = v.strip()
        if not v:
            raise ValueError("Пароль не может состоять только из пробелов")
        if len(v) < 6:
            raise ValueError("Пароль должен содержать минимум 6 символов")
        
        # Проверка на нелатинские символы
        if re.search(r'[^\x00-\x7F]', v):
            if re.search(r'[а-яА-ЯёЁ]', v):
                raise ValueError("Пароль может содержать только латинские буквы, цифры и специальные символы. Кириллица не допускается.")
            else:
                raise ValueError("Пароль может содержать только латинские буквы, цифры и специальные символы. Другие символы не допускаются.")
        
        if not re.match(r'^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]+$', v):
            raise ValueError("Пароль может содержать только латинские буквы, цифры и специальные символы")
        
        v_bytes = v.encode('utf-8')
        if len(v_bytes) > 72:
            raise ValueError("Пароль слишком длинный (максимум 72 байта в UTF-8)")
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError("Пароль должен содержать хотя бы одну латинскую букву")
        if not re.search(r'[0-9]', v):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        return v


class ChangePasswordRequest(BaseModel):
    """Запрос на изменение пароля"""
    old_password: str = Field(..., description="Старый пароль")
    new_password: str = Field(..., min_length=6, max_length=72, description="Новый пароль")
    
    @field_validator('old_password')
    @classmethod
    def validate_old_password(cls, v: str) -> str:
        """Валидация старого пароля"""
        if not v:
            raise ValueError("Пароль не может быть пустым")
        v = v.strip()
        if not v:
            raise ValueError("Пароль не может состоять только из пробелов")
        v_bytes = v.encode('utf-8')
        if len(v_bytes) > 72:
            raise ValueError("Пароль слишком длинный (максимум 72 байта в UTF-8)")
        return v
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Валидация нового пароля"""
        if not v:
            raise ValueError("Пароль не может быть пустым")
        v = v.strip()
        if not v:
            raise ValueError("Пароль не может состоять только из пробелов")
        if len(v) < 6:
            raise ValueError("Пароль должен содержать минимум 6 символов")
        
        # Проверка на нелатинские символы
        if re.search(r'[^\x00-\x7F]', v):
            if re.search(r'[а-яА-ЯёЁ]', v):
                raise ValueError("Пароль может содержать только латинские буквы, цифры и специальные символы. Кириллица не допускается.")
            else:
                raise ValueError("Пароль может содержать только латинские буквы, цифры и специальные символы. Другие символы не допускаются.")
        
        if not re.match(r'^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]+$', v):
            raise ValueError("Пароль может содержать только латинские буквы, цифры и специальные символы")
        
        v_bytes = v.encode('utf-8')
        if len(v_bytes) > 72:
            raise ValueError("Пароль слишком длинный (максимум 72 байта в UTF-8)")
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError("Пароль должен содержать хотя бы одну латинскую букву")
        if not re.search(r'[0-9]', v):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        return v


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
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Проверка, существует ли пользователь
    if User.exists(request.username, db=db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже существует"
        )
    
    # Создание пользователя
    try:
        user = User.create(
            username=request.username,
            password=request.password,
            secret_code=request.secret_code,
            db=db
        )
    except ValueError as e:
        logger.error(f"Ошибка создания пользователя {request.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Неожиданная ошибка при создании пользователя {request.username}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании пользователя. Попробуйте позже."
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
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Вход в систему"""
    # Загрузка пользователя
    user = User(request.username, db=db)
    if not user.load(db=db):
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
    user.update_last_login(db=db)
    
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
async def recover_password(request: RecoverPasswordRequest, db: Session = Depends(get_db)):
    """Восстановление пароля по секретному коду"""
    # Загрузка пользователя
    user = User(request.username, db=db)
    if not user.load(db=db):
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
    user.save(db=db)
    
    return {"message": "Пароль успешно изменён"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить информацию о текущем пользователе"""
    user = User(username, db=db)
    if not user.load(db=db):
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
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Изменить пароль (требует аутентификации)"""
    user = User(username, db=db)
    if not user.load(db=db):
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
    user.save(db=db)
    
    return {"message": "Пароль успешно изменён"}


class UpdateUsernameRequest(BaseModel):
    """Запрос на изменение имени пользователя"""
    new_username: str = Field(..., min_length=3, max_length=50, description="Новое имя пользователя")
    
    @field_validator('new_username')
    @classmethod
    def validate_new_username(cls, v: str) -> str:
        """Валидация нового username"""
        if not v:
            raise ValueError("Имя пользователя не может быть пустым")
        
        v = v.strip()
        
        if not v:
            raise ValueError("Имя пользователя не может состоять только из пробелов")
        
        if len(v) < 3:
            raise ValueError("Имя пользователя должно содержать минимум 3 символа")
        
        if len(v) > 50:
            raise ValueError("Имя пользователя не может быть длиннее 50 символов")
        
        # Строгая проверка: только латинские буквы, цифры, подчеркивание и дефис
        if re.search(r'[^\x00-\x7F]', v):
            if re.search(r'[а-яА-ЯёЁ]', v):
                raise ValueError(
                    "Имя пользователя может содержать только латинские буквы (a-z, A-Z), цифры (0-9), подчеркивание (_) и дефис (-). Кириллица и другие нелатинские символы не допускаются."
                )
            else:
                raise ValueError(
                    "Имя пользователя может содержать только латинские буквы (a-z, A-Z), цифры (0-9), подчеркивание (_) и дефис (-). Другие символы не допускаются."
                )
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError(
                "Имя пользователя может содержать только латинские буквы (a-z, A-Z), цифры (0-9), подчеркивание (_) и дефис (-). Другие символы не допускаются."
            )
        
        if v.startswith('-') or v.startswith('_') or v.endswith('-') or v.endswith('_'):
            raise ValueError("Имя пользователя не может начинаться или заканчиваться дефисом или подчеркиванием")
        
        if v.isdigit():
            raise ValueError("Имя пользователя не может состоять только из цифр")
        
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError("Имя пользователя должно содержать хотя бы одну латинскую букву")
        
        return v


class DeleteAccountRequest(BaseModel):
    """Запрос на удаление аккаунта"""
    password: str = Field(..., description="Пароль для подтверждения удаления")


@router.put("/username", status_code=status.HTTP_200_OK)
async def update_username(
    request: UpdateUsernameRequest,
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Изменить имя пользователя"""
    import shutil
    from pathlib import Path
    from backend.config import settings
    
    user = User(username, db=db)
    if not user.load(db=db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    try:
        old_username = user.update_username(request.new_username, db=db)
        
        # Переименовываем директорию с персональными миссиями
        old_missions_dir = settings.MISSIONS_DIR / "personal" / old_username
        new_missions_dir = settings.MISSIONS_DIR / "personal" / request.new_username
        
        if old_missions_dir.exists():
            if new_missions_dir.exists():
                # Если новая директория уже существует, объединяем содержимое
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Директория {new_missions_dir} уже существует, объединяем содержимое")
                # Перемещаем содержимое из старой в новую
                for item in old_missions_dir.iterdir():
                    dest = new_missions_dir / item.name
                    if dest.exists():
                        # Если файл уже существует, пропускаем
                        continue
                    shutil.move(str(item), str(dest))
                # Удаляем старую директорию
                old_missions_dir.rmdir()
            else:
                # Просто переименовываем
                old_missions_dir.rename(new_missions_dir)
        
        # Переименовываем файл прогресса
        old_progress_file = settings.SANDBOX_DATA_DIR / f"progress_{old_username}.json"
        new_progress_file = settings.SANDBOX_DATA_DIR / f"progress_{request.new_username}.json"
        
        if old_progress_file.exists() and not new_progress_file.exists():
            old_progress_file.rename(new_progress_file)
        
        return {
            "message": "Имя пользователя успешно изменено",
            "old_username": old_username,
            "new_username": request.new_username
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка изменения имени пользователя: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при изменении имени пользователя"
        )


@router.delete("/account", status_code=status.HTTP_200_OK)
async def delete_account(
    request: DeleteAccountRequest = Body(...),
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удалить аккаунт пользователя"""
    import shutil
    from pathlib import Path
    from backend.config import settings
    from backend.sandbox.container import ContainerManager
    
    user = User(username, db=db)
    if not user.load(db=db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Проверка пароля
    if not user.verify_password(request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный пароль"
        )
    
    try:
        # Удаляем персональные миссии
        personal_missions_dir = settings.MISSIONS_DIR / "personal" / username
        if personal_missions_dir.exists():
            shutil.rmtree(personal_missions_dir)
        
        # Удаляем файл прогресса
        progress_file = settings.SANDBOX_DATA_DIR / f"progress_{username}.json"
        if progress_file.exists():
            progress_file.unlink()
        
        # Останавливаем и удаляем активные контейнеры пользователя
        try:
            container_manager = ContainerManager()
            # Получаем все контейнеры пользователя
            containers = container_manager.list_containers()
            for container_id in containers:
                try:
                    container = container_manager.get_container(container_id)
                    if container and container.username == username:
                        container_manager.stop_container(container_id)
                        container_manager.remove_container(container_id)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Ошибка удаления контейнера {container_id}: {e}")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Ошибка при очистке контейнеров: {e}")
        
        # Удаляем пользователя из БД
        user.delete(db=db)
        
        return {"message": "Аккаунт успешно удалён"}
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка удаления аккаунта: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении аккаунта"
        )


@router.get("/secret-code-info", status_code=status.HTTP_200_OK)
async def get_secret_code_info(
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить информацию о секретном коде (без самого кода)"""
    user = User(username, db=db)
    if not user.load(db=db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Проверяем, установлен ли секретный код
    has_secret_code = user.secret_code_hash is not None
    
    return {
        "has_secret_code": has_secret_code,
        "message": "Секретный код установлен" if has_secret_code else "Секретный код не установлен"
    }

