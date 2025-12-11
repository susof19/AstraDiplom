"""Роуты для работы с песочницами"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel

from backend.sandbox.manager import sandbox_manager

router = APIRouter()


class CreateSandboxRequest(BaseModel):
    mission_id: str
    level: str
    image: str = "localhost/astra-linux:se"  # Используем localhost/ для локальных образов


@router.post("/sandbox/create")
async def create_sandbox(request: CreateSandboxRequest) -> Dict[str, Any]:
    """Создать песочницу для миссии"""
    sandbox = await sandbox_manager.create_sandbox(
        request.mission_id,
        request.level,
        request.image
    )
    
    if not sandbox:
        raise HTTPException(status_code=500, detail="Не удалось создать песочницу")
    
    info = await sandbox.get_info()
    
    return {
        "mission_id": request.mission_id,
        "container_name": sandbox.container_name,
        "container_id": sandbox.container_id,
        "status": sandbox.status,
        "vnc_port": sandbox.vnc_port,
        "info": info
    }


@router.get("/sandbox/{mission_id}")
async def get_sandbox(mission_id: str) -> Dict[str, Any]:
    """Получить информацию о песочнице"""
    sandbox = await sandbox_manager.get_sandbox(mission_id)
    
    if not sandbox:
        raise HTTPException(status_code=404, detail="Песочница не найдена")
    
    info = await sandbox.get_info()
    
    return {
        "mission_id": mission_id,
        "container_name": sandbox.container_name,
        "container_id": sandbox.container_id,
        "status": sandbox.status,
        "vnc_port": sandbox.vnc_port,
        "info": info
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

