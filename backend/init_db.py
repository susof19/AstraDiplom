#!/usr/bin/env python3
"""Скрипт инициализации базы данных PostgreSQL"""
import sys
from pathlib import Path

# Добавляем родительскую директорию в PYTHONPATH
backend_dir = Path(__file__).parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))

from backend.database import init_db, engine, Base
from backend.models.user_db import User  # Импортируем для регистрации модели в Base
from backend.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Инициализация базы данных"""
    logger.info("🔧 Инициализация базы данных PostgreSQL...")
    logger.info(f"📋 URL базы данных: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'скрыт'}")
    
    try:
        # Проверка соединения
        logger.info("🔍 Проверка соединения с базой данных...")
        with engine.connect() as conn:
            logger.info("✅ Соединение с базой данных установлено")
        
        # Создание таблиц
        logger.info("📦 Создание таблиц...")
        init_db()
        logger.info("✅ Таблицы созданы успешно")
        
        logger.info("")
        logger.info("✅ База данных инициализирована успешно!")
        logger.info("")
        logger.info("💡 Созданные таблицы:")
        logger.info("   - users (пользователи)")
        logger.info("")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации базы данных: {e}")
        logger.error("")
        logger.error("💡 Проверьте:")
        logger.error("   1. PostgreSQL установлен и запущен")
        logger.error("   2. База данных создана")
        logger.error("   3. Пользователь и пароль корректны")
        logger.error("   4. DATABASE_URL в .env или config.py правильный")
        sys.exit(1)


if __name__ == "__main__":
    main()

