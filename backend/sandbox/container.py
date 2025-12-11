"""Контейнерная песочница на базе Podman (Astra Linux)"""
import asyncio
import json
import subprocess
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from backend.config import settings

logger = logging.getLogger(__name__)


class ContainerSandbox:
    """Управление изолированным контейнером для миссии"""
    
    def __init__(self, mission_id: str, level: str, image: str = "localhost/astra-linux:se"):
        self.mission_id = mission_id
        self.level = level
        # Нормализуем имя образа: если нет префикса, добавляем localhost/
        if "/" not in image and ":" in image:
            self.image = f"localhost/{image}"
        else:
            self.image = image
        self.container_name = f"astra-trainer-{mission_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.container_id: Optional[str] = None
        self.vnc_port: Optional[int] = None
        self.status: str = "created"
        
    async def create(self) -> bool:
        """Создать контейнер (Astra Linux rootless режим)"""
        try:
            # Определяем базовую команду
            # В Astra Linux для rootless может использоваться rootlessenv
            base_cmd = settings.PODMAN_BINARY.split()
            
            # Определяем параметры в зависимости от уровня
            cmd = base_cmd + [
                "run",
                "-d",
                "--name", self.container_name,
                "--rm",  # Автоудаление при остановке
                "--memory", settings.SANDBOX_MEMORY_LIMIT,
                "--cpus", settings.SANDBOX_CPU_LIMIT,
            ]
            
            # Для rootless режима в Astra Linux
            if settings.PODMAN_ROOTLESS:
                # В rootless режиме некоторые опции могут отличаться
                # label=disable может не работать, используем другие опции
                cmd.extend([
                    "--userns=keep-id",  # Сохранить UID/GID пользователя
                ])
            else:
                cmd.extend([
                    "--security-opt", "label=disable",
                ])
            
            # Для уровня A добавляем GUI (VNC)
            if self.level == "A":
                # Находим свободный порт
                self.vnc_port = await self._find_free_port(settings.VNC_PORT_START)
                cmd.extend([
                    "-p", f"{self.vnc_port}:5900",
                    "-e", "DISPLAY=:0",
                ])
            
            # Монтируем read-only миссию и данные
            mission_dir = settings.MISSIONS_DIR / f"level_{self.level.lower()}" / self.mission_id
            if mission_dir.exists():
                cmd.extend([
                    "-v", f"{mission_dir}:/mission:ro",
                ])
            
            # Добавляем образ
            cmd.append(self.image)
            
            # Запускаем контейнер
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                logger.error(f"Ошибка создания контейнера: {stderr.decode()}")
                return False
            
            self.container_id = stdout.decode().strip()
            self.status = "running"
            logger.info(f"Контейнер создан: {self.container_name} ({self.container_id})")
            return True
            
        except Exception as e:
            logger.error(f"Исключение при создании контейнера: {e}")
            return False
    
    async def start(self) -> bool:
        """Запустить контейнер"""
        if not self.container_id:
            return await self.create()
        
        try:
            result = await asyncio.create_subprocess_exec(
                settings.PODMAN_BINARY,
                "start",
                self.container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            
            if result.returncode == 0:
                self.status = "running"
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка запуска контейнера: {e}")
            return False
    
    async def stop(self) -> bool:
        """Остановить контейнер"""
        if not self.container_id:
            return True
        
        try:
            result = await asyncio.create_subprocess_exec(
                settings.PODMAN_BINARY,
                "stop",
                self.container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            
            self.status = "stopped"
            return True
        except Exception as e:
            logger.error(f"Ошибка остановки контейнера: {e}")
            return False
    
    async def remove(self) -> bool:
        """Удалить контейнер"""
        if not self.container_id:
            return True
        
        try:
            result = await asyncio.create_subprocess_exec(
                settings.PODMAN_BINARY,
                "rm",
                "-f",
                self.container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            
            self.status = "removed"
            self.container_id = None
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления контейнера: {e}")
            return False
    
    async def exec_command(self, command: str, user: str = "root") -> tuple[str, int]:
        """Выполнить команду в контейнере"""
        if not self.container_id:
            return "", 1
        
        try:
            result = await asyncio.create_subprocess_exec(
                settings.PODMAN_BINARY,
                "exec",
                "-u", user,
                self.container_name,
                "sh", "-c", command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            return stdout.decode() + stderr.decode(), result.returncode
        except Exception as e:
            logger.error(f"Ошибка выполнения команды: {e}")
            return str(e), 1
    
    async def get_info(self) -> Dict[str, Any]:
        """Получить информацию о контейнере"""
        if not self.container_id:
            return {}
        
        try:
            result = await asyncio.create_subprocess_exec(
                settings.PODMAN_BINARY,
                "inspect",
                self.container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            data = json.loads(stdout.decode())
            return data[0] if data else {}
        except Exception as e:
            logger.error(f"Ошибка получения информации: {e}")
            return {}
    
    async def _find_free_port(self, start_port: int) -> int:
        """Найти свободный порт"""
        import socket
        port = start_port
        while port < start_port + 100:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result != 0:
                return port
            port += 1
        raise RuntimeError("Не удалось найти свободный порт")

