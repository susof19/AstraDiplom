"""Менеджер песочниц"""
import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

from backend.sandbox.container import ContainerSandbox
from backend.config import settings

if settings.MOCK_SANDBOX:
    from backend.sandbox.mock_sandbox import MockSandbox

logger = logging.getLogger(__name__)


class SandboxManager:
    """Управление жизненным циклом песочниц"""
    
    def __init__(self):
        self.sandboxes: Dict[str, ContainerSandbox] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def create_sandbox(self, mission_id: str, level: str, image: str = None, use_vnc: bool = True, distro: str = None) -> Optional[ContainerSandbox]:
        """Создать новую песочницу для миссии"""
        logger.info(f"[MANAGER] === Создание песочницы: mission_id={mission_id}, level={level}, image={image}, use_vnc={use_vnc}, distro={distro} ===")
        existing = self.sandboxes.get(mission_id)
        if existing:
            logger.info(f"[MANAGER] Найдена существующая песочница для {mission_id}, status={existing.status}, удаляем...")
            try:
                await existing.remove()
                logger.info(f"[MANAGER] ✅ Старая песочница для {mission_id} удалена")
            except Exception as e:
                logger.warning(f"[MANAGER] Ошибка при удалении старой песочницы: {e}")
            finally:
                # Удаляем из словаря в любом случае
                if mission_id in self.sandboxes:
                    del self.sandboxes[mission_id]
                    logger.info(f"[MANAGER] Песочница {mission_id} удалена из менеджера")
        
        if settings.MOCK_SANDBOX:
            sandbox = MockSandbox(mission_id, level, image, use_vnc)
        else:
            sandbox = ContainerSandbox(mission_id, level, image, use_vnc, distro)
        
        logger.info(f"[MANAGER] Вызов sandbox.create() для миссии {mission_id}")
        create_result = await sandbox.create()
        logger.info(f"[MANAGER] Результат sandbox.create(): {create_result}")
        
        if create_result:
            if use_vnc and (level.upper() in ["A", "B"] or sandbox.use_vnc):
                logger.info(f"Ожидание запуска VNC сервера для миссии {mission_id}...")
                vnc_ready = await sandbox.wait_for_vnc(timeout=60)
                if not vnc_ready:
                    logger.warning(f"VNC сервер не запустился для миссии {mission_id}")
            
            self.sandboxes[mission_id] = sandbox
            logger.info(f"Песочница создана для миссии {mission_id}")
            return sandbox
        else:
            error_msg = getattr(sandbox, '_last_error', None) or "Не удалось создать песочницу"
            logger.error(f"Не удалось создать песочницу для миссии {mission_id}: {error_msg}")
            # Сохраняем ошибку в sandbox для последующего использования
            raise Exception(error_msg)
    
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
                await asyncio.sleep(60)
                
                now = datetime.now()
                expired = []
                
                for mission_id, sandbox in list(self.sandboxes.items()):
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


sandbox_manager = SandboxManager()

