"""Роуты для проверки миссий"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from backend.grader.checker import Grader
from backend.sandbox.manager import sandbox_manager

router = APIRouter()


@router.post("/grader/check/{mission_id}")
async def check_mission(mission_id: str, level: str, user_id: str = "default") -> Dict[str, Any]:
    """Проверить выполнение миссии"""
    from backend.models.progress import get_user_progress
    
    sandbox = await sandbox_manager.get_sandbox(mission_id)
    
    if not sandbox:
        raise HTTPException(status_code=404, detail="Песочница не найдена")
    
    result = await Grader.grade_mission(mission_id, level, sandbox)
    
    # Сохраняем прогресс, если миссия выполнена
    if result.get("result") in ["passed", "partial"]:
        score = result.get("score", 0)
        progress = get_user_progress(user_id)
        progress.complete_mission(mission_id, level, score)
        result["new_achievements"] = progress.achievements
    
    return result

