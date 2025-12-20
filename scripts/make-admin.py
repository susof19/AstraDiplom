#!/usr/bin/env python3
"""Скрипт для назначения пользователя администратором"""
import sys
from pathlib import Path

# Добавляем родительскую директорию в PYTHONPATH
backend_dir = Path(__file__).parent.parent / "backend"
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))

from backend.database import get_db
from backend.models.user_db import User


def main():
    if len(sys.argv) < 2:
        print("Использование: python scripts/make-admin.py <username>")
        print("Пример: python scripts/make-admin.py admin")
        sys.exit(1)
    
    username = sys.argv[1]
    
    db = next(get_db())
    try:
        user = User(username, db=db)
        if not user.load(db=db):
            print(f"❌ Пользователь '{username}' не найден")
            sys.exit(1)
        
        if user.is_admin:
            print(f"✅ Пользователь '{username}' уже является администратором")
        else:
            user.is_admin = 1
            user.save(db=db)
            print(f"✅ Пользователь '{username}' теперь администратор")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
