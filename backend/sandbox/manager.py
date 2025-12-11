"""Менеджер песочниц"""
import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

from backend.sandbox.container import ContainerSandbox
from backend.config import settings

# Импорт mock-реализации для режима разработки
if settings.MOCK_SANDBOX:
    from backend.sandbox.mock_sandbox import MockSandbox

logger = logging.getLogger(__name__)


class SandboxManager:
    """Управление жизненным циклом песочниц"""
    
    def __init__(self):
        self.sandboxes: Dict[str, ContainerSandbox] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def create_sandbox(self, mission_id: str, level: str, image: str = "localhost/astra-linux:se", use_vnc: bool = True) -> Optional[ContainerSandbox]:
        """Создать новую песочницу для миссии"""
        # Проверяем, нет ли уже активной песочницы для этой миссии
        existing = self.sandboxes.get(mission_id)
        if existing and existing.status == "running":
            logger.warning(f"Песочница для миссии {mission_id} уже существует")
            return existing
        
        # Удаляем старую, если есть
        if existing:
            await existing.remove()
        
        # Создаём новую (используем mock в режиме разработки)
        if settings.MOCK_SANDBOX:
            sandbox = MockSandbox(mission_id, level, image, use_vnc)
        else:
            sandbox = ContainerSandbox(mission_id, level, image, use_vnc)
        
        if await sandbox.create():
            # Для GUI миссий ждём готовности VNC
            if use_vnc and (level == "A" or sandbox.use_vnc):
                logger.info(f"Ожидание запуска VNC сервера для миссии {mission_id}...")
                vnc_ready = await sandbox.wait_for_vnc(timeout=60)
                if not vnc_ready:
                    logger.warning(f"VNC сервер не запустился для миссии {mission_id}")
            
            self.sandboxes[mission_id] = sandbox
            logger.info(f"Песочница создана для миссии {mission_id}")
            return sandbox
        else:
            logger.error(f"Не удалось создать песочницу для миссии {mission_id}")
            return None
    
    async def get_sandbox(self, mission_id: str) -> Optional[ContainerSandbox]:
        """Получить песочницу по ID миссии"""
        return self.sandboxes.get(mission_id)
    
    async def remove_sandbox(self, mission_id: str) -> bool:
        """Удалить песочницу"""
        sandbox = self.sandboxes.get(mission_id)
        if sandbox:
            await sandbox.remove()
            del self.sandboxes[mission_id]
            return True
        return False
    
    async def cleanup_expired(self):
        """Очистка истёкших песочниц"""
        while True:
            try:
                await asyncio.sleep(60)  # Проверка каждую минуту
                
                now = datetime.now()
                expired = []
                
                for mission_id, sandbox in list(self.sandboxes.items()):
                    # TODO: добавить отслеживание времени создания
                    # Пока просто проверяем статус
                    if sandbox.status in ["stopped", "removed"]:
                        expired.append(mission_id)
                
                for mission_id in expired:
                    await self.remove_sandbox(mission_id)
                    logger.info(f"Удалена истёкшая песочница: {mission_id}")
                    
            except Exception as e:
                logger.error(f"Ошибка при очистке песочниц: {e}")
    
    def start_cleanup_task(self):
        """Запустить задачу очистки"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self.cleanup_expired())


# Глобальный менеджер
sandbox_manager = SandboxManager()

