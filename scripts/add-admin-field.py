#!/usr/bin/env python3
"""Скрипт для добавления поля is_admin в существующую таблицу users"""
import sys
from pathlib import Path

# Добавляем родительскую директорию в PYTHONPATH
backend_dir = Path(__file__).parent.parent / "backend"
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))

from backend.database import engine, Base
from backend.models.user_db import User  # Импортируем для регистрации модели
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Добавить поле is_admin в таблицу users если его нет"""
    logger.info("🔧 Проверка и добавление поля is_admin в таблицу users...")
    
    try:
        with engine.begin() as conn:  # Используем begin() для автоматического commit/rollback
            # Проверяем, существует ли поле is_admin
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='is_admin'
            """))
            
            if result.fetchone():
                logger.info("✅ Поле is_admin уже существует")
            else:
                logger.info("📦 Добавление поля is_admin...")
                # Добавляем поле is_admin с значением по умолчанию 0
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0
                """))
                logger.info("✅ Поле is_admin успешно добавлено")
        
        logger.info("")
        logger.info("✅ Миграция завершена успешно!")
        logger.info("")
        logger.info("💡 Теперь вы можете назначить пользователя администратором:")
        logger.info("   python scripts/make-admin.py <username>")
        logger.info("")
        
    except Exception as e:
        logger.error(f"❌ Ошибка миграции: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
