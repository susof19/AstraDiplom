"""Модель пользователя с использованием PostgreSQL"""
from datetime import datetime
from typing import Optional, Dict
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from backend.database import UserModel, get_db
from backend.config import settings

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def truncate_to_72_bytes(text: str) -> str:
    """Обрезать строку до 72 байт, сохраняя валидность UTF-8"""
    text_bytes = text.encode('utf-8')
    if len(text_bytes) <= 72:
        return text
    # Обрезаем до 72 байт
    text_bytes = text_bytes[:72]
    # Убираем неполные UTF-8 последовательности в конце
    while text_bytes and (text_bytes[-1] & 0xC0) == 0x80:
        text_bytes = text_bytes[:-1]
    return text_bytes.decode('utf-8', errors='ignore')


class User:
    """Модель пользователя с использованием PostgreSQL"""
    
    def __init__(self, username: str, db: Optional[Session] = None):
        self.username = username
        self._db = db
        self.password_hash: Optional[str] = None
        self.secret_code_hash: Optional[str] = None
        self.created_at: Optional[datetime] = None
        self.last_login: Optional[datetime] = None
        self.id: Optional[int] = None
        
    def _get_db(self) -> Session:
        """Получить сессию БД"""
        if self._db:
            return self._db
        # Если сессия не передана, создаем новую (для обратной совместимости)
        from backend.database import SessionLocal
        return SessionLocal()
    
    def load(self, db: Optional[Session] = None) -> bool:
        """Загрузить данные пользователя из базы данных"""
        session = db or self._get_db()
        try:
            user_model = session.query(UserModel).filter(UserModel.username == self.username).first()
            if not user_model:
                return False
            
            self.id = user_model.id
            self.password_hash = user_model.password_hash
            self.secret_code_hash = user_model.secret_code_hash
            self.created_at = user_model.created_at
            self.last_login = user_model.last_login
            return True
        except Exception as e:
            print(f"Ошибка загрузки пользователя {self.username}: {e}")
            return False
        finally:
            if not db and not self._db:
                session.close()
    
    def save(self, db: Optional[Session] = None):
        """Сохранить данные пользователя в базу данных"""
        session = db or self._get_db()
        try:
            if self.id:
                # Обновление существующего пользователя
                user_model = session.query(UserModel).filter(UserModel.id == self.id).first()
                if user_model:
                    user_model.password_hash = self.password_hash
                    user_model.secret_code_hash = self.secret_code_hash
                    user_model.last_login = self.last_login
            else:
                # Создание нового пользователя
                user_model = UserModel(
                    username=self.username,
                    password_hash=self.password_hash,
                    secret_code_hash=self.secret_code_hash,
                    created_at=self.created_at or datetime.utcnow(),
                    last_login=self.last_login
                )
                session.add(user_model)
            
            session.commit()
            if not self.id:
                # Получаем ID после создания
                session.refresh(user_model)
                self.id = user_model.id
        except Exception as e:
            session.rollback()
            print(f"Ошибка сохранения пользователя {self.username}: {e}")
            raise
        finally:
            if not db and not self._db:
                session.close()
    
    def set_password(self, password: str):
        """Установить хеш пароля"""
        # bcrypt имеет ограничение в 72 байта, обрезаем если необходимо
        password = truncate_to_72_bytes(password)
        self.password_hash = pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """Проверить пароль"""
        if not self.password_hash:
            return False
        # bcrypt имеет ограничение в 72 байта, обрезаем если необходимо
        password = truncate_to_72_bytes(password)
        return pwd_context.verify(password, self.password_hash)
    
    def set_secret_code(self, secret_code: str):
        """Установить хеш секретного кода"""
        # bcrypt имеет ограничение в 72 байта, обрезаем если необходимо
        secret_code = truncate_to_72_bytes(secret_code)
        self.secret_code_hash = pwd_context.hash(secret_code)
    
    def verify_secret_code(self, secret_code: str) -> bool:
        """Проверить секретный код"""
        if not self.secret_code_hash:
            return False
        # bcrypt имеет ограничение в 72 байта, обрезаем если необходимо
        secret_code = truncate_to_72_bytes(secret_code)
        return pwd_context.verify(secret_code, self.secret_code_hash)
    
    def update_last_login(self, db: Optional[Session] = None):
        """Обновить время последнего входа"""
        self.last_login = datetime.utcnow()
        self.save(db)
    
    def to_dict(self) -> Dict:
        """Преобразовать в словарь (без паролей)"""
        return {
            "username": self.username,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
    
    @staticmethod
    def exists(username: str, db: Optional[Session] = None) -> bool:
        """Проверить, существует ли пользователь"""
        session = db or User._get_db_static()
        try:
            user_model = session.query(UserModel).filter(UserModel.username == username).first()
            return user_model is not None
        finally:
            if not db:
                session.close()
    
    @staticmethod
    def _get_db_static() -> Session:
        """Статический метод для получения сессии БД"""
        from backend.database import SessionLocal
        return SessionLocal()
    
    @staticmethod
    def create(username: str, password: str, secret_code: str, db: Optional[Session] = None) -> 'User':
        """Создать нового пользователя"""
        session = db or User._get_db_static()
        try:
            if User.exists(username, db=session):
                raise ValueError(f"Пользователь {username} уже существует")
            
            user = User(username, db=session)
            user.set_password(password)
            user.set_secret_code(secret_code)
            user.created_at = datetime.utcnow()
            user.save(db=session)
            return user
        finally:
            if not db:
                session.close()

