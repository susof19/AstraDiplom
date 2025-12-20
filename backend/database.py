"""Настройка базы данных"""
from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Generator

from backend.config import settings

# Создание базового класса для моделей
Base = declarative_base()


class UserModel(Base):
    """Модель пользователя в базе данных"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    secret_code_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    is_admin = Column(Integer, default=0, nullable=False)  # 0 = обычный пользователь, 1 = администратор


# Создание движка базы данных
# Добавляем параметры кодировки для правильной работы с UTF-8
database_url = settings.DATABASE_URL
if '?' not in database_url:
    # Добавляем параметры кодировки, если их еще нет
    database_url += "?client_encoding=utf8"
elif 'client_encoding' not in database_url:
    database_url += "&client_encoding=utf8"

engine = create_engine(
    database_url,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    echo=False,  # Установить True для отладки SQL запросов
    connect_args={
        "options": "-c client_encoding=utf8"
    }
)

# Создание фабрики сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    """Генератор для получения сессии базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Инициализация базы данных (создание таблиц)"""
    Base.metadata.create_all(bind=engine)

