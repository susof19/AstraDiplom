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
    
    # Podman настройки (Astra Linux)
    # В Astra Linux используется rootless режим через rootless-helper-astra
    # Для работы используется команда rootlessenv (аналог rootlessenv для Docker)
    PODMAN_BINARY: str = "podman"  # Или "rootlessenv podman" для rootless режима
    PODMAN_ROOTLESS: bool = True  # Использовать rootless режим
    PODMAN_SOCKET: str = "unix:///run/user/1000/podman/podman.sock"  # rootless socket
    # Для Astra Linux с rootless-helper-astra может потребоваться:
    # PODMAN_BINARY: str = "rootlessenv podman"  # Если используется rootless-helper-astra
    
    # Sandbox настройки
    SANDBOX_TIMEOUT: int = 3600  # секунд
    SANDBOX_MEMORY_LIMIT: str = "2G"
    SANDBOX_CPU_LIMIT: str = "2"
    
    # VNC/noVNC настройки
    VNC_PORT_START: int = 5900
    NOVNC_PORT_START: int = 6080
    VNC_PASSWORD: str = "astra123"  # TODO: генерировать случайно
    VNC_RESOLUTION: str = "1280x720"
    
    # API настройки
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    
    # Безопасность
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Режим разработки (для Windows/тестирования без Podman)
    MOCK_SANDBOX: bool = False  # Использовать mock-песочницы вместо реальных контейнеров
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

