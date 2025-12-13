"""Mock-реализация песочницы для разработки на Windows"""
import asyncio
import random
from typing import Optional, Dict, Any
from datetime import datetime

from backend.sandbox.container import ContainerSandbox

logger = __import__("logging").getLogger(__name__)


class MockSandbox(ContainerSandbox):
    """Mock-реализация песочницы для тестирования без Podman"""
    
    def __init__(self, mission_id: str, level: str, image: str = None, use_vnc: bool = True, distro: str = None):
        super().__init__(mission_id, level, image, use_vnc, distro)
        self.container_id = f"mock-{mission_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Mock VNC порты
        if use_vnc or level == "A":
            self.vnc_port = 5900 + random.randint(1, 100)
            self.novnc_port = 6080 + random.randint(1, 100)
        else:
            self.vnc_port = None
            self.novnc_port = None
            
        self._mock_files: Dict[str, str] = {}  # Mock файловая система
        self._mock_processes: list = []
        
    async def create(self) -> bool:
        """Создать mock-контейнер"""
        logger.info(f"Создание mock-песочницы для миссии {self.mission_id}")
        await asyncio.sleep(0.5)  # Имитация задержки
        self.status = "running"
        return True
    
    async def start(self) -> bool:
        """Запустить mock-контейнер"""
        self.status = "running"
        return True
    
    async def stop(self) -> bool:
        """Остановить mock-контейнер"""
        self.status = "stopped"
        return True
    
    async def remove(self) -> bool:
        """Удалить mock-контейнер"""
        self.status = "removed"
        self.container_id = None
        return True
    
    async def exec_command(self, command: str, user: str = "root") -> tuple[str, int]:
        """Выполнить команду в mock-контейнере"""
        logger.debug(f"Mock команда: {command}")
        
        # Имитация некоторых команд
        if "test -f" in command:
            # Извлечь путь из команды
            path = command.split("'")[1] if "'" in command else command.split('"')[1] if '"' in command else ""
            exists = path in self._mock_files
            return ("exists" if exists else "not_found", 0 if exists else 1)
        
        elif "cat" in command:
            path = command.split("'")[1] if "'" in command else command.split('"')[1] if '"' in command else ""
            if path in self._mock_files:
                return (self._mock_files[path], 0)
            return ("", 1)
        
        elif "which" in command:
            # Имитация which
            cmd = command.split()[-1]
            return (f"/usr/bin/{cmd}\n", 0)
        
        elif "find" in command and ".docx" in command:
            # Имитация find для миссии organize_files
            count = len([f for f in self._mock_files.keys() if f.endswith(".docx")])
            return (f"{count}\n", 0)
        
        elif "wc -l" in command:
            # Имитация wc -l
            return ("5\n", 0)
        
        elif "grep" in command:
            # Имитация grep
            return ("matched\n", 0)
        
        elif "ps aux" in command or "awk" in command:
            # Имитация ps aux
            return ("", 0)
        
        elif "systemctl" in command:
            if "is-active" in command:
                return ("active\n", 0)
            elif "is-enabled" in command:
                return ("enabled\n", 0)
            return ("", 0)
        
        elif "ufw status" in command:
            # Имитация ufw status
            return ("Status: active\n80/tcp ALLOW\n22/tcp ALLOW\n", 0)
        
        elif "curl" in command:
            # Имитация curl
            return ("HTTP/1.1 200 OK\n", 0)
        
        elif "test -x" in command:
            # Имитация проверки исполняемости
            return ("executable\n", 0)
        
        # По умолчанию - успешное выполнение
        return ("", 0)
    
    async def get_info(self) -> Dict[str, Any]:
        """Получить информацию о mock-контейнере"""
        info = {
            "Id": self.container_id,
            "Name": self.container_name,
            "State": {"Status": self.status},
            "Config": {"Image": self.image},
            "NetworkSettings": {
                "Ports": {
                    "5900/tcp": [{"HostPort": str(self.vnc_port)}] if self.vnc_port else None,
                    "6080/tcp": [{"HostPort": str(self.novnc_port)}] if self.novnc_port else None
                }
            }
        }
        
        # Добавляем информацию о VNC
        if self.vnc_port or self.novnc_port:
            info["vnc_info"] = {
                "vnc_port": self.vnc_port,
                "novnc_port": self.novnc_port,
                "novnc_url": f"http://localhost:{self.novnc_port}/vnc.html" if self.novnc_port else None,
                "enabled": True
            }
        
        return info
    
    async def get_vnc_url(self) -> Optional[str]:
        """Получить URL для подключения к noVNC (mock)"""
        if not self.novnc_port:
            return None
        from backend.config import settings
        password = settings.VNC_PASSWORD
        return f"http://localhost:{self.novnc_port}/vnc.html?password={password}&autoconnect=true&resize=scale"
    
    async def wait_for_vnc(self, timeout: int = 60) -> bool:
        """Ожидание готовности VNC сервера (mock - всегда готов)"""
        await asyncio.sleep(1)  # Имитация задержки
        return True if self.novnc_port else False
    
    def set_mock_file(self, path: str, content: str = ""):
        """Установить mock-файл для тестирования"""
        self._mock_files[path] = content
    
    def remove_mock_file(self, path: str):
        """Удалить mock-файл"""
        if path in self._mock_files:
            del self._mock_files[path]

