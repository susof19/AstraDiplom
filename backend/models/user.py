"""Модель пользователя"""
# Импортируем модель из user_db для работы с PostgreSQL
from backend.models.user_db import User

# Экспортируем для обратной совместимости
__all__ = ["User"]
