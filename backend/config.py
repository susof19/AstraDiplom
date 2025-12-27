"""Конфигурация приложения"""
import os
from pydantic_settings import BaseSettings
from pathlib import Path

# Определяем BASE_DIR до создания класса
BASE_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Пути
    BASE_DIR: Path = BASE_DIR
    MISSIONS_DIR: Path = BASE_DIR / "missions"
    IMAGES_DIR: Path = BASE_DIR / "images"
    SANDBOX_DATA_DIR: Path = BASE_DIR / "sandbox_data"
    
    # Podman/Docker настройки
    # Поддерживает rootless режим для Podman (Debian, Ubuntu, Astra Linux)
    # Для работы используется команда podman или docker
    PODMAN_BINARY: str = "podman"  # Или "docker" для Docker, "rootlessenv podman" для Astra Linux с rootless-helper-astra
    PODMAN_ROOTLESS: bool = True  # Использовать rootless режим (для Podman)
    PODMAN_SOCKET: str = "unix:///run/user/1000/podman/podman.sock"  # rootless socket для Podman
    # Для Astra Linux с rootless-helper-astra может потребоваться:
    # PODMAN_BINARY: str = "rootlessenv podman"  # Если используется rootless-helper-astra
    
    # Sandbox настройки
    SANDBOX_TIMEOUT: int = 3600  # секунд
    SANDBOX_MEMORY_LIMIT: str = "2G"
    SANDBOX_CPU_LIMIT: str = "2"
    
    # VNC/noVNC настройки
    VNC_PORT_START: int = 5900
    NOVNC_PORT_START: int = 6080
    VNC_PASSWORD: str = "sandbox123"
    VNC_RESOLUTION: str = "1280x720"
    
    # API настройки
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    
    # Безопасность
    # Разрешаем подключения с localhost и локальной сети
    # Для доступа с других машин в локальной сети добавьте их IP адреса
    # Можно переопределить через переменную окружения ALLOWED_ORIGINS (JSON массив)
    # или добавить дополнительные через ADDITIONAL_ORIGINS (разделенные запятой)
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    JWT_SECRET_KEY: str = "IHateItAll"  # В продакшене через .env
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7
    
    # Режим разработки (для Windows/тестирования без Podman)
    MOCK_SANDBOX: bool = False  # Использовать mock-песочницы вместо реальных контейнеров
    
    # Выбор дистрибутива для песочниц
    # Поддерживаемые: debian, ubuntu, astra
    DEFAULT_DISTRO: str = "debian"  # Дистрибутив по умолчанию
    # Маппинг дистрибутивов на базовые образы
    # Для B/C миссий используются стандартные образы из Docker Hub
    # Для astra используется debian как fallback, так как astra-linux:se требует debootstrap
    DISTRO_BASE_IMAGES: dict[str, str] = {
        "debian": "debian:12",
        "ubuntu": "ubuntu:22.04",
        "astra": "debian:12"  # Используем debian как fallback для astra в B/C миссиях (astra-linux:se требует debootstrap)
    }
    # Маппинг дистрибутивов на GUI образы (с VNC)
    DISTRO_GUI_IMAGES: dict[str, str] = {
        "debian": "localhost/linux-gui-vnc:debian",
        "ubuntu": "localhost/linux-gui-vnc:ubuntu",
        # Для Astra Linux используется образ из репозитория shinbatsu/astra-ui-vnc-container
        # Если он недоступен, используйте вместо этого: "localhost/linux-gui-vnc:astra"
        # (создается через: ./scripts/create-astra-image.sh --vnc, вариант 5)
        "astra": "localhost/astra-vnc:latest"
    }
    
    # База данных PostgreSQL
    DATABASE_URL: str = "postgresql://trainer_user:trainer_password@localhost:5432/trainer_db"
    # Формат: postgresql://user:password@host:port/database
    # Можно переопределить через переменную окружения DATABASE_URL или .env файл
    
    class Config:
        # .env файл должен находиться в директории backend/
        # pydantic-settings ищет .env относительно текущей рабочей директории
        # или можно указать явный путь через env_file
        env_file = str(BASE_DIR / "backend" / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

# Добавляем дополнительные origins из переменной окружения после создания экземпляра
additional_origins = os.getenv("ADDITIONAL_ORIGINS", "")
if additional_origins:
    for origin in additional_origins.split(","):
        origin = origin.strip()
        if origin and origin not in settings.ALLOWED_ORIGINS:
            settings.ALLOWED_ORIGINS.append(origin)

