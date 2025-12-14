"""Роуты для работы с песочницами"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel

from backend.sandbox.manager import sandbox_manager

router = APIRouter()


class CreateSandboxRequest(BaseModel):
    mission_id: str
    level: str
    image: Optional[str] = None  # Опционально: если не указан, выбирается автоматически по distro
    use_vnc: bool = True  # Включить VNC по умолчанию
    distro: Optional[str] = None  # Дистрибутив: debian, ubuntu, astra (по умолчанию из config)


@router.post("/sandbox/create")
async def create_sandbox(request: CreateSandboxRequest) -> Dict[str, Any]:
    """Создать песочницу для миссии"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Создание песочницы: mission_id={request.mission_id}, level={request.level}, "
                f"image={request.image}, use_vnc={request.use_vnc}, distro={request.distro}")
    
    sandbox = await sandbox_manager.create_sandbox(
        request.mission_id,
        request.level,
        request.image,
        request.use_vnc,
        request.distro
    )
    
    if not sandbox:
        raise HTTPException(status_code=500, detail="Не удалось создать песочницу")
    
    info = await sandbox.get_info()
    vnc_url = await sandbox.get_vnc_url() if sandbox.use_vnc else None
    
    return {
        "mission_id": request.mission_id,
        "container_name": sandbox.container_name,
        "container_id": sandbox.container_id,
        "status": sandbox.status,
        "vnc_port": sandbox.vnc_port,
        "novnc_port": sandbox.novnc_port,
        "vnc_url": vnc_url,
        "info": info
    }


@router.get("/sandbox/active")
async def get_active_sandbox() -> Dict[str, Any]:
    """Получить активную песочницу (первую запущенную)"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Запрос активной песочницы. Всего песочниц: {len(sandbox_manager.sandboxes)}")
    
    # Ищем первую запущенную песочницу
    for mission_id, sandbox in sandbox_manager.sandboxes.items():
        logger.info(f"Проверка песочницы {mission_id}: status={sandbox.status}")
        if sandbox.status == "running":
            info = await sandbox.get_info()
            logger.info(f"Найдена активная песочница: {mission_id}")
            return {
                "has_active": True,
                "mission_id": mission_id,
                "container_name": sandbox.container_name,
                "container_id": sandbox.container_id,
                "status": sandbox.status
            }
    
    logger.info("Активная песочница не найдена")
    return {"has_active": False}


@router.get("/sandbox/{mission_id}")
async def get_sandbox(mission_id: str) -> Dict[str, Any]:
    """Получить информацию о песочнице"""
    sandbox = await sandbox_manager.get_sandbox(mission_id)
    
    if not sandbox:
        raise HTTPException(status_code=404, detail="Песочница не найдена")
    
    info = await sandbox.get_info()
    vnc_url = await sandbox.get_vnc_url() if hasattr(sandbox, 'use_vnc') and sandbox.use_vnc else None
    
    return {
        "mission_id": mission_id,
        "container_name": sandbox.container_name,
        "container_id": sandbox.container_id,
        "status": sandbox.status,
        "vnc_port": sandbox.vnc_port,
        "novnc_port": getattr(sandbox, 'novnc_port', None),
        "vnc_url": vnc_url,
        "info": info
    }


@router.get("/sandbox/{mission_id}/vnc")
async def get_vnc_info(mission_id: str) -> Dict[str, Any]:
    """Получить информацию о VNC подключении"""
    sandbox = await sandbox_manager.get_sandbox(mission_id)
    
    if not sandbox:
        raise HTTPException(status_code=404, detail="Песочница не найдена")
    
    if not hasattr(sandbox, 'use_vnc') or not sandbox.use_vnc:
        raise HTTPException(status_code=400, detail="VNC не включен для этой песочницы")
    
    vnc_url = await sandbox.get_vnc_url()
    
    if not vnc_url:
        raise HTTPException(status_code=503, detail="VNC сервер не готов")
    
    return {
        "mission_id": mission_id,
        "vnc_port": sandbox.vnc_port,
        "novnc_port": sandbox.novnc_port,
        "vnc_url": vnc_url,
        "ready": True
    }


@router.post("/sandbox/{mission_id}/stop")
async def stop_sandbox(mission_id: str) -> Dict[str, Any]:
    """Остановить песочницу"""
    sandbox = await sandbox_manager.get_sandbox(mission_id)
    
    if not sandbox:
        raise HTTPException(status_code=404, detail="Песочница не найдена")
    
    success = await sandbox.stop()
    
    if not success:
        raise HTTPException(status_code=500, detail="Не удалось остановить песочницу")
    
    return {"status": "stopped", "mission_id": mission_id}


@router.delete("/sandbox/{mission_id}")
async def remove_sandbox(mission_id: str) -> Dict[str, Any]:
    """Удалить песочницу"""
    success = await sandbox_manager.remove_sandbox(mission_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Песочница не найдена")
    
    return {"status": "removed", "mission_id": mission_id}


@router.post("/sandbox/{mission_id}/exec")
async def exec_command(mission_id: str, command: str) -> Dict[str, Any]:
    """Выполнить команду в песочнице"""
    sandbox = await sandbox_manager.get_sandbox(mission_id)
    
    if not sandbox:
        raise HTTPException(status_code=404, detail="Песочница не найдена")
    
    output, code = await sandbox.exec_command(command)
    
    return {
        "output": output,
        "exit_code": code,
        "command": command
    }


@router.get("/sandbox/copy_file")
async def copy_file_get() -> Dict[str, Any]:
    """
    Эндпоинт для копирования файлов (legacy/stub)
    Файлы копируются автоматически при монтировании /mission в контейнер
    """
    return {
        "message": "Файлы автоматически доступны в контейнере через /mission",
        "note": "Используйте монтирование тома при создании песочницы"
    }


@router.get("/sandbox/{mission_id}/processes")
async def get_processes(mission_id: str) -> Dict[str, Any]:
    """Получить список процессов в контейнере"""
    sandbox = await sandbox_manager.get_sandbox(mission_id)
    
    if not sandbox:
        raise HTTPException(status_code=404, detail="Песочница не найдена")
    
    if sandbox.status != "running":
        raise HTTPException(status_code=400, detail="Песочница не запущена")
    
    # Выполняем ps aux для получения процессов
    output, code = await sandbox.exec_command("ps aux", user="root")
    
    if code != 0:
        raise HTTPException(status_code=500, detail="Не удалось получить список процессов")
    
    # Парсим вывод ps aux
    lines = output.strip().split('\n')
    processes = []
    
    # Пропускаем заголовок
    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 11:
            processes.append({
                "user": parts[0],
                "pid": parts[1],
                "cpu": parts[2],
                "mem": parts[3],
                "command": ' '.join(parts[10:])
            })
    
    return {
        "count": len(processes),
        "processes": processes
    }


@router.get("/sandbox/{mission_id}/filesystem")
async def get_filesystem(mission_id: str, path: str = "/root") -> Dict[str, Any]:
    """Получить информацию о файловой системе контейнера"""
    sandbox = await sandbox_manager.get_sandbox(mission_id)
    
    if not sandbox:
        raise HTTPException(status_code=404, detail="Песочница не найдена")
    
    if sandbox.status != "running":
        raise HTTPException(status_code=400, detail="Песочница не запущена")
    
    # Получаем использование диска
    df_output, df_code = await sandbox.exec_command("df -h /", user="root")
    
    # Получаем содержимое директории
    ls_output, ls_code = await sandbox.exec_command(f"ls -lah '{path}' 2>&1", user="root")
    
    return {
        "disk_usage": df_output if df_code == 0 else "Не удалось получить информацию",
        "directory_listing": ls_output if ls_code == 0 else f"Ошибка: {ls_output}"
    }


@router.get("/sandbox/{mission_id}/network")
async def get_network(mission_id: str) -> Dict[str, Any]:
    """Получить сетевую информацию контейнера"""
    sandbox = await sandbox_manager.get_sandbox(mission_id)
    
    if not sandbox:
        raise HTTPException(status_code=404, detail="Песочница не найдена")
    
    if sandbox.status != "running":
        raise HTTPException(status_code=400, detail="Песочница не запущена")
    
    # Получаем сетевые интерфейсы
    ifconfig_output, ifconfig_code = await sandbox.exec_command("ip addr show 2>&1 || ifconfig 2>&1", user="root")
    
    # Получаем открытые порты
    netstat_output, netstat_code = await sandbox.exec_command(
        "ss -tuln 2>&1 || netstat -tuln 2>&1", user="root"
    )
    
    # Получаем активные соединения
    connections_output, connections_code = await sandbox.exec_command(
        "ss -tn 2>&1 || netstat -tn 2>&1", user="root"
    )
    
    return {
        "interfaces": ifconfig_output if ifconfig_code == 0 else "Не удалось получить информацию",
        "listening_ports": netstat_output if netstat_code == 0 else "Не удалось получить информацию",
        "active_connections": connections_output if connections_code == 0 else "Не удалось получить информацию"
    }

