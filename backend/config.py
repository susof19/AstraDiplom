"""Конфигурация приложения"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Пути
    BASE_DIR: Path = Path(__file__).parent.parent
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
    VNC_PASSWORD: str = "sandbox123"  # TODO: генерировать случайно
    VNC_RESOLUTION: str = "1280x720"
    
    # API настройки
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    
    # Безопасность
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    JWT_SECRET_KEY: str = "astra-linux-training-simulator-secret-key-change-in-production"  # В продакшене через .env
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7
    
    # Режим разработки (для Windows/тестирования без Podman)
    MOCK_SANDBOX: bool = False  # Использовать mock-песочницы вместо реальных контейнеров
    
    # База данных PostgreSQL
    DATABASE_URL: str = "postgresql://trainer_user:trainer_password@localhost:5432/trainer_db"
    # Формат: postgresql://user:password@host:port/database
    # Можно переопределить через переменную окружения DATABASE_URL или .env файл
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

