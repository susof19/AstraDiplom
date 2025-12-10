"""Скрипт запуска для разработки из директории backend"""
import sys
import os
from pathlib import Path

# Добавляем родительскую директорию в PYTHONPATH
backend_dir = Path(__file__).parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))

# Теперь можно импортировать
if __name__ == "__main__":
    import uvicorn
    from backend.api.main import app
    from backend.config import settings
    
    # Устанавливаем переменную окружения для mock режима, если она задана
    if os.environ.get("MOCK_SANDBOX"):
        os.environ["MOCK_SANDBOX"] = "true"
    
    # Запускаем uvicorn с правильной конфигурацией
    uvicorn.run(
        "backend.api.main:app",  # Используем строку импорта для reload
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        reload_dirs=[str(backend_dir), str(project_root / "backend")]
    )

